use axum::{
    Router,
    extract::{Json as ExtractJson, State},
    response::Json,
    routing::post,
};
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::json;

use std::net::SocketAddr;
use std::process::Command;
use std::sync::Arc;

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
        .route("/", post(push_handler))
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

#[derive(Debug, Deserialize)]
struct Prompt {
    prompt: String,
    model: String,
    uuid: String,
}

async fn push_handler(
    State(state): State<AppState>,
    ExtractJson(payload): ExtractJson<PushData>,
) -> Json<serde_json::Value> {
    tokio::spawn(handle_prompt_request(payload, state)); //new thread so we can respond
    Json(json!({ "status": "success"}))
}

async fn handle_prompt_request(data: PushData, state: AppState) {
    let (stop_tx, stop_rx) = oneshot::channel::<()>();
    let mut port_no = 0;
    for (model, port) in state.models.iter() {
        if model == &data.model {
            port_no = *port;
        }
    }

    let model_request = tokio::spawn(call_model(data.original, port_no));
    let nvidia_thread = tokio::spawn(async move { nvidia(stop_rx, port_no) });

    //end when we get network
    let _ = model_request.await;
    let _ = stop_tx.send(()); //kills nvidia thread
    let _ = nvidia_thread.await;
}

async fn call_model(original: String, model_port: u16) {
    let parsed: Prompt = serde_json::from_str(&original).expect("Invalid JSON");
}

async fn nvidia(mut stop_rx: tokio::sync::oneshot::Receiver<()>, port: u16) {
    println!("started query for nvidia");
    let mut cmd = Command::new("nvidia-smi");
    cmd.arg("--query-gpu=uuid,name,utilization.gpu,utilization.memory,memory.used,power.draw,temperature.gpu");
    cmd.arg("--format=csv,noheader,nounits");

    // let client = reqwest::blocking::Client::new();
    loop {
        tokio::select! {
            _ = &mut stop_rx => {
                println!("killing nvidia query");
                break;
            }
            _ = sleep(Duration::from_secs(1)) => {
                let output = cmd.output().expect("unable to execute nvidia_smi");
                // let _resp = client.post("http://localhost:3833")
                //     .body(String::from_utf8(output.stdout).unwrap());
            }
        }
    }
}
