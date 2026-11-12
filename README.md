# PDF Question Answering

A Streamlit application for indexing PDFs and asking questions about them. It keeps the existing RAG stack: MarkItDown, LangChain's `RecursiveCharacterTextSplitter`, Hugging Face `all-MiniLM-L6-v2` embeddings, ChromaDB, and Groq's `openai/gpt-oss-20b` model.

## Run locally

1. Use Python 3.11.
2. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv .venv
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   # macOS/Linux: source .venv/bin/activate
   python -m pip install -r requirements-dev.txt
   ```

3. Copy `.env.example` to `.env` and set `GROQ_API_KEY` to a valid Groq API key. Keep `.env` private; it is excluded from Git and Docker build contexts.
4. Start the UI:

   ```bash
   streamlit run app.py
   ```

Open <http://localhost:8501>. The first indexing operation downloads the embedding model. Indexed vectors are stored in `./chroma_db`; uploaded PDFs are stored in `./data/uploads`.

The original command-line workflows remain available:

```bash
python ingest.py
python query.py "What does the document say?"
```

`ingest.py` expects `data/document.pdf`.

## Run with Docker Compose

Create `.env` as described above, then run:

```bash
docker compose up --build -d
```

Open <http://localhost:8501>. Compose persists the Chroma database, uploaded PDFs, and Hugging Face model cache in named volumes. The app listens on port 8501 and runs as a non-root user. Stop it with `docker compose down`; named-volume data is retained. To remove the data too, explicitly remove the `rag_data` and `huggingface_cache` volumes.

## Tests

```bash
python -m pytest -q
```

The tests mock external model and vector-store calls; they do not need a Groq key or download the embedding model.

## Deploy to AWS EC2 with GitHub Actions

The workflow at `.github/workflows/ci-cd.yml` runs tests, builds and pushes `ghcr.io/<owner>/<repository>` with `latest` and commit-SHA tags, and deploys `latest` after a push to `main`. Pull requests run tests but do not publish or deploy.

### One-time EC2 setup

1. Push this project to a GitHub repository whose deployment branch is `main`.
2. Launch an Ubuntu EC2 instance. In its security group, allow inbound SSH (TCP 22) from your GitHub Actions runner and TCP port 8501 only from the addresses that need app access. GitHub-hosted runner IPs can change; a self-hosted runner with fixed egress makes SSH allowlisting easier. For a public production service, use HTTPS through a reverse proxy or load balancer rather than exposing Streamlit directly.
3. Connect as the intended deployment user, clone the repository (for example, `git clone <repository-url> ~/pdf-rag-source`), and run `bash ~/pdf-rag-source/deploy/setup-ec2.sh`. Log out and back in after it adds that user to the Docker group.
4. Create `~/pdf-rag/.env` on EC2 with `GROQ_API_KEY=<your key>` and restrict it with `chmod 600 ~/pdf-rag/.env`. Do not put this file in the repository. The deployment script preserves this file while updating the app.
5. Add these repository Actions secrets:
   - `EC2_HOST`: the instance's public DNS name or IP.
   - `EC2_USER`: the Ubuntu deployment username.
   - `EC2_SSH_KEY`: the private SSH key corresponding to the EC2 user's authorized key.
6. Ensure Actions are enabled and push to `main`. The workflow uses the automatically provided `GITHUB_TOKEN` with package write permission to publish to GHCR and log in on EC2; no additional registry secret is required. The EC2 instance needs outbound access to GHCR and the Groq API.

The workflow waits for the container's health check and fails if the deployment does not become healthy. Deployment requires the EC2 host, SSH access, Docker, the `.env` file, and GitHub Actions secrets to be configured; creating this workflow alone does not deploy the application.

## Configuration and security

- `GROQ_API_KEY` is required when asking questions. It is read from the process environment or a local `.env` file.
- `CHROMA_PATH` defaults to `./chroma_db`; `RAG_DATA_DIR` defaults to `./data`.
- Uploaded PDFs are limited to 20 MB each.
- If an API key was previously exposed in source or chat, revoke it and create a replacement before deploying.
