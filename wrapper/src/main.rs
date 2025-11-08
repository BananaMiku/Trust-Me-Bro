use axum::{
    Error, Router,
    extract::{Json as ExtractJson, State},
    http::header,
    response::{IntoResponse, Json},
    routing::{get, post},
};
use http_body_util::BodyExt;
use hyper::{Request, Uri};
use hyper::{
    Response,
    body::{Bytes, Incoming},
};
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::json;

use std::net::SocketAddr;
use std::process::Command;
use std::sync::Arc;

use hyper_util::rt::TokioIo;
use tokio::net::TcpStream;
use tokio::sync::oneshot;
use tokio::time::{Duration, sleep};

#[derive(Clone)]
struct AppState {
    models: Arc<Vec<(String, u16)>>,
}

#[tokio::main]
async fn main() {
    // Get command-line args
    let models_str = std::env::args().nth(1).expect("no file name");
    let port_no = std::env::args().nth(2).expect("no port no");

    let re = Regex::new(r"([a-zA-Z]+),([0-9]+);").unwrap();
    let mut models = vec![];

    for cap in re.captures_iter(&models_str) {
        let model = cap.get(1).unwrap().as_str().to_string();
        let port = cap.get(2).unwrap().as_str().parse::<u16>().unwrap();
        models.push((model, port));
    }

    println!("Parsed models: {:?}", models);

    let state = AppState {
        models: Arc::new(models),
    };

    let app = Router::new()
        .route("/", get(push_handler))
        .with_state(state);

    let port: u16 = port_no.parse().expect("Invalid port number");
    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    println!("Listening on http://{}", addr);

    // Run server
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}

#[derive(Debug, Deserialize)]
struct PushData {
    original: String,
    uuid: String,
    model: String,
}

async fn push_handler(
    State(state): State<AppState>,
    ExtractJson(payload): ExtractJson<PushData>,
) -> impl IntoResponse {
    let (stop_tx, stop_rx) = oneshot::channel::<()>();
    let mut port_no = 0;
    for (model, port) in state.models.iter() {
        if model == &payload.model {
            port_no = *port;
        }
    }

    let model_request = tokio::spawn(call_model(payload.original, port_no));
    let nvidia_thread = tokio::spawn(nvidia(stop_rx, payload.uuid, payload.model, port_no));

    //end when we get network
    // let res = model_request.await;
    let _ = stop_tx.send(()); //kills nvidia thread
    let _ = nvidia_thread.await;

    // if let Ok(res) = res {
    //     return (
    //         [(header::CONTENT_TYPE, "application/json")],
    //         format!("{:?}", res.into_body()),
    //     );
    // }
    // (
    //     [(header::CONTENT_TYPE, "application/json")],
    //     String::from("{\"message\": \"died\"}"),
    // )

    (
        [(header::CONTENT_TYPE, "application/json")],
        "{\"messages\": [{\"role\": \"user\", \"content\": \"hi\"}, {\"role\": \"assistant\", \"content\": \"hi\"}]}",
    )
}

async fn call_model(original: String, model_port: u16) -> Response<Incoming> {
    let url = format!("http://127.0.0.1:{}", model_port);
    let stream = TcpStream::connect(url.clone()).await.unwrap();
    let io = TokioIo::new(stream);
    let (mut sender, _conn) = hyper::client::conn::http1::handshake(io).await.unwrap();

    let authority = url.parse::<Uri>().unwrap().authority().unwrap().clone();

    // Create an HTTP request with an empty body and a HOST header
    let req = Request::builder()
        .uri(url.clone())
        .header(hyper::header::HOST, authority.as_str())
        .body(http_body_util::Full::new(Bytes::from(original)))
        .unwrap();

    // Await the response...
    println!("sending req");
    let res = sender.send_request(req).await.unwrap();

    println!("Response status: {}", res.status());
    res
}

async fn nvidia(
    mut stop_rx: tokio::sync::oneshot::Receiver<()>,
    uuid: String,
    model: String,
    port: u16,
) {
    println!("started query for nvidia");

    /*
    let mut ss = Command::new("ss");
    ss.arg("-lptn");
    ss.arg(format!("'sport= :{}'", port));

    // get pid
    let output = ss.output().expect("couldn't find port");
    let output_s = String::from_utf8(output.stdout).unwrap();
    let re = Regex::new(r"pid=(\d+)").unwrap();
    let pid = re
        .captures_iter(&output_s)
        .next()
        .expect("no pid found")
        .get(0)
        .expect("no pid found")
        .as_str();

    let mut smi = Command::new("nvidia-smi");
    smi.arg("--query-gpu=uuid,name,utilization.gpu,utilization.memory,memory.used,power.draw,temperature.gpu");
    smi.arg("--format=csv,noheader,nounits");
    smi.arg(format!("--query-compute-apps={}", pid));
    */

    let url = "http://localhost:3833".parse::<Uri>().unwrap();
    let stream = TcpStream::connect("localhost:3833").await.unwrap();
    let io = TokioIo::new(stream);

    let (mut sender, conn) = hyper::client::conn::http1::handshake(io).await.unwrap();
    tokio::task::spawn(async move {
        if let Err(err) = conn.await {
            println!("Connection failed: {:?}", err);
        }
    });

    loop {
        tokio::select! {
            _ = &mut stop_rx => {
                println!("killing nvidia query");
                break;
            }
            _ = sleep(Duration::from_secs(1)) => {
                // let smi_out = String::from_utf8(smi.output().expect("unable to execute nvidia_smi").stdout).unwrap();
                let smi_out = "GPU-09dfe69f-a29c-c23f-35a4-c5b79af54d34, NVIDIA GeForce RTX 4080 SUPER, 1, 0, 642, 5.57, 35";
                let items: Vec<&str> = smi_out.split(", ").collect();

                let authority = "http://localhost:3833".parse::<Uri>().unwrap().authority().unwrap().clone();

                let report = format!("{{\"gpuUtilization\": {}, \"vramUsage\": {}, \"powerDraw\": {}, \"uuid\": {{\"userID\": \"{}\", \"model\": \"{}\"}}",
                    items.get(2).unwrap(),
                    items.get(5).unwrap(),
                    items.get(6).unwrap(), uuid, model);

                // Create an HTTP request with an empty body and a HOST header
                let req = Request::builder()
                    .uri(url.clone())
                    .header(hyper::header::HOST, authority.as_str())
                    .body(http_body_util::Full::new(Bytes::from(report))).unwrap();

                // Await the response...
                let res = sender.send_request(req).await.unwrap();

                println!("Response status: {}", res.status());
            }
        }
    }
}
