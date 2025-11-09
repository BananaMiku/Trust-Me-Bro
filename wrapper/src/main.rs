use axum::{
    Error, Router,
    extract::{Json as ExtractJson, State},
    http::header,
    response::{IntoResponse, Json, Response},
    routing::{get, post},
};
use http_body_util::BodyExt;
use hyper::body::{Bytes, Incoming};
use hyper::{Request, Uri};
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::json;

use std::process::Command;
use std::sync::Arc;
use std::{net::SocketAddr, process::Stdio};

use hyper_util::rt::TokioIo;
use tokio::net::TcpStream;
use tokio::sync::Mutex;
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

    let state = AppState {
        models: Arc::new(models),
    };

    let app = Router::new()
        .route("/", get(push_handler))
        .with_state(state);

    let port: u16 = port_no.parse().expect("Invalid port number");
    let addr = SocketAddr::from(([127, 0, 0, 1], port));

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
) -> Response<String> {
    let (stop_tx, stop_rx) = oneshot::channel::<()>();
    let mut port_no = 0;
    for (model, port) in state.models.iter() {
        if model == &payload.model {
            port_no = *port;
        }
    }

    let model_request = tokio::spawn(call_model(payload.original, port_no));
    // let nvidia_thread = tokio::spawn(nvidia(stop_rx, payload.uuid, payload.model, port_no));

    //end when we get network
    sleep(Duration::from_millis(1_500)).await;
    let res = model_request.await;
    let _ = stop_tx.send(()); //kills nvidia thread
    // let _ = nvidia_thread.await;

    if let Ok(res) = res {
        axum::response::Response::builder()
            .header("Content-Type", "application/json")
            .body(
                String::from_utf8(res.into_body().collect().await.unwrap().to_bytes().to_vec())
                    .unwrap(),
            )
            .unwrap()
    } else {
        axum::response::Response::builder()
            .status(500)
            .body(String::from(""))
            .unwrap()
    }
}

async fn call_model(original: String, model_port: u16) -> hyper::Response<Incoming> {
<<<<<<< HEAD
    print!("calling model");
    let url = format!("http://localhost:{}/v1/chat/completion", model_port);
    let stream = TcpStream::connect(&url).await.unwrap();
=======
    //let stream = TcpStream::connect(format!("localhost:{}", model_port))
    let stream = TcpStream::connect("localhost:3222").await.unwrap();
>>>>>>> 0221465 (ifixex things)
    let io = TokioIo::new(stream);
    let (mut sender, conn) = hyper::client::conn::http1::handshake(io).await.unwrap();
    tokio::task::spawn(async move {
        if let Err(err) = conn.await {
            println!("Connection failed: {:?}", err);
        }
    });

    let url = format!("http://localhost:{}/v1/chat/completions", model_port);
    let authority = url.parse::<Uri>().unwrap().authority().unwrap().clone();

    // Create an HTTP request with an empty body and a HOST header
    let req = Request::builder()
        .method("POST")
        .uri("/v1/chat/completions")
        .header(hyper::header::HOST, authority.as_str())
        .body(http_body_util::Full::new(Bytes::from(original)))
        .unwrap();

    // Await the response...
    let res = sender.send_request(req).await.unwrap();

<<<<<<< HEAD
    println!("Model Response status: {}", res.status());
=======
    println!("Response status: {}", res.status());
    println!("rust response!! {:?}", res.body());
>>>>>>> 0221465 (ifixex things)
    res.into()
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

    let url = "http://localhost:3823/metrics".parse::<Uri>().unwrap();
    let url_finished = "http://localhost:3823/finished".parse::<Uri>().unwrap();

    let mutex = Mutex::new(0);

    loop {
        tokio::select! {
            _ = &mut stop_rx => {
                println!("killing nvidia query");
                let stream = TcpStream::connect("localhost:3823").await.unwrap();
                let io = TokioIo::new(stream);
                let (mut sender, conn) = hyper::client::conn::http1::handshake(io).await.unwrap();
                tokio::task::spawn(async move {
                    if let Err(err) = conn.await {
                        println!("Connection failed: {:?}", err);
                    }
                });
                let authority = url_finished.authority().unwrap().clone();
                let req = Request::builder()
                    .method("POST")
                    .uri("/finished")
                    .header(hyper::header::HOST, authority.as_str())
                    .header(hyper::header::CONTENT_TYPE, "application/json")
                    .body(http_body_util::Full::new(Bytes::from(format!("{{\"userID\": \"{}\"}}", uuid)))).unwrap();

                let mut lock = mutex.lock().await;
                sleep(Duration::from_millis(500)).await;
                let _res = sender.send_request(req).await.unwrap();

                *lock += 1;

                break;
            }
            _ = sleep(Duration::from_secs(1)) => {

                // let mut ts = Command::new("tegrastats")
                //     .arg("--interval")
                //     .arg("1")
                //     .stdout(Stdio::piped())
                //     .spawn().unwrap();
                let mut ts = Command::new("echo")
                    .arg("'11-09-2025 00:00:29 RAM 3058/7620MB (lfb 37x4MB) CPU [somestuff] GR 12% cpu soc soc gpu tj soc VDDIN 5080mW/5080mW VDD_CPU 603mW/603mW VDD_SOC 1449mW/1449mW'")
                    .stdout(Stdio::piped())
                    .spawn().unwrap();

                let head = Command::new("head")
                    .arg("-n")
                    .arg("1")
                    .stdin(Stdio::from(ts.stdout.take().unwrap()))
                    .stdout(Stdio::piped())
                    .spawn().unwrap();

                let output = head.wait_with_output().unwrap();
                let ts_out = str::from_utf8(&output.stdout).unwrap();

                let items: Vec<&str> = ts_out.split(" ").collect();
                let rams_s: &str = items.get(3).unwrap();
                let nums: Vec<f64> = rams_s[..rams_s.find('M').unwrap()]
                    .split('/')
                    .map(|x| x.parse::<f64>().unwrap())
                    .collect();
                let ram = nums[0] / nums[1];
                let gpu = items.get(9).unwrap().trim_end_matches('%').parse::<f64>().unwrap() / 100.0;
                let draw_s: &str = items.get(21).unwrap();
                let draw = draw_s[..draw_s.find('m').unwrap()].parse::<f64>().unwrap();

                // 3 is ram
                // 8 is GPU utilization
                // 16 is VIN
                // 20 is VDD_SOC

                let stream = TcpStream::connect("localhost:3823").await.unwrap();
                let io = TokioIo::new(stream);
                let (mut sender, conn) = hyper::client::conn::http1::handshake(io).await.unwrap();
                tokio::task::spawn(async move {
                    if let Err(err) = conn.await {
                        println!("Connection failed: {:?}", err);
                    }
                });
                let authority = url.authority().unwrap().clone();
                let report = format!("{{\"gpuUtilization\": {}, \"vramUsage\": {}, \"powerDraw\": {}, \"uuid\": {{\"userID\": \"{}\", \"model\": \"{}\"}}}}",
                    gpu, ram, draw, uuid, model);

                println!("nvidia report: {}", report);

                // Create an HTTP request with an empty body and a HOST header
                let req = Request::builder()
                    .method("POST")
                    .uri("/metrics")
                    .header(hyper::header::HOST, authority.as_str())
                    .header(hyper::header::CONTENT_TYPE, "application/json")
                    .body(http_body_util::Full::new(Bytes::from(report))).unwrap();

                // Await the response...
                let mut lock = mutex.lock().await;
                let res = sender.send_request(req).await.unwrap();

                *lock += 1;

                println!("Nvidia Response status: {}", res.status());
            }
        }
    }
}
