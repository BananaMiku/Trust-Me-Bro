use axum::{routing::post, Router, response::Json, extract::Json as ExtractJson};
use serde_json::json;
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use regex::Regex;

#[tokio::main]
async fn main() {
    // Get command-line args
    let models_str = std::env::args().nth(1).expect("no file name");
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
    let task1 = tokio::spawn(async {
        //put way to query model
        fn1("Message 1").await;
    });

    let task2 = tokio::spawn(async {
        //nvidia pull
        fn2("Message 2").await;
    });

    // Wait for both tasks to finish
    let (res1, res2) = join!(task1, task2);
    //send to our server 
}

