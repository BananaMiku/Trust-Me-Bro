use axum::{routing::post, Router, response::Json, extract::Json as ExtractJson};
use serde_json::json;
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use regex::Regex;
use tokio::sync::oneshot;
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() {
    // Get command-line args
    let models_str = std::env::args().nth(1).expect("no model port str");
    let port_no = std::env::args().nth(2).expect("no port no");

    // Parse models
    let re = Regex::new(r"([a-zA-Z]+),([0-9]+);").unwrap();
    let mut models = vec![];
    for cap in re.captures_iter(&models_str) {
        let model = cap.get(1).unwrap().as_str();
        let port = cap.get(2).unwrap().as_str().parse::<u16>().unwrap();
        models.push((model.to_string(), port));
    }
    println!("Parsed models: {:?}", models);

    let app = Router::new().route("/", post(push_handler));
    

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
    model: String
}

async fn push_handler(ExtractJson(payload): ExtractJson<PushData>) -> Json<serde_json::Value> {
    tokio::spawn(handle_prompt_request(payload)); //new thread so we can respond
    Json(json!({ "status": "success"}))
}

async fn handle_prompt_request(data: PushData) {
    let (stop_tx, stop_rx) = oneshot::channel::<()>();
    let task1 = tokio::spawn(call_model());
    let nvidia_thread = tokio::spawn(async move {nvidia(stop_rx)});

    //end when we get network
    let _ = task1.await;
    let _ = stop_tx.send(()); //kills nvidia thread
    let _ = nvidia_thread.await;

}

async fn call_model(){
}

async fn nvidia(mut stop_rx : tokio::sync::oneshot::Receiver<()>) {
    println!("started query for nvidia");
    loop {
        tokio::select! {
            _ = &mut stop_rx => {
                println!("killing nvidia query");
                break;
            }
            _ = sleep(Duration::from_secs(1)) => {
                println!("query nvidia");
            }
        }
    }
}
