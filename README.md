# SneakerHead: E-commerce Site → MongoDB Atlas → Databricks Delta Pipeline

A small end-to-end data project. A sneaker storefront (Node.js + Express) collects checkout form submissions, stores them in **MongoDB Atlas**, and a **Databricks** notebook incrementally loads them into a **Delta table**. The website is hosted on **AWS EC2** behind **nginx** and runs in **Docker**.

> **Dummy project.** The card number, expiry and CVV fields exist only to simulate a checkout. Use fake values only. Never enter real card details, and never store a real CVV.

---

## Demo

<!--
Add your video here:
1. Click the pencil icon on this README on GitHub.
2. Drag Ecom_demo.mp4 into the editor at this spot (free accounts: about 10 MB limit).
3. GitHub inserts the link. Commit.
If the file is too big, upload to YouTube and use:
[![Demo](docs/thumbnail.png)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)
-->

**What the demo shows**

1. Website deployed on AWS EC2 and opened via the public IP
2. Checkout form submitted, and the record appears in MongoDB Atlas (`mydb.users`)
3. Databricks pipeline runs and loads the new records into the Delta table `users_bronze`

---

## Architecture

```
┌──────────┐   HTTP   ┌───────────────┐  proxy  ┌──────────────────────┐
│ Browser  │ ───────► │ EC2           │ ──────► │ Docker: Node/Express │
└──────────┘          │ port 80/443   │         │ port 3000            │
                      └───────────────┘         └──────────┬───────────┘
                                                           │ Mongoose
                                                           ▼
                                                ┌────────────────────┐
                                                │ MongoDB Atlas (M0) │
                                                │ mydb.users         │
                                                └──────────┬─────────┘
                                                           │ pymongo (incremental,
                                                           │ filtered on createdAt)
                                                           ▼
                                                ┌────────────────────┐
                                                │ Databricks notebook│
                                                │ MERGE into Delta   │
                                                │ table users_bronze │
                                                └────────────────────┘
```

## Tech stack

| Layer | Tools |
|---|---|
| Frontend | HTML, CSS, vanilla JavaScript |
| Backend | Node.js, Express, Mongoose, dotenv |
| Database | MongoDB Atlas (free M0 cluster) |
| Hosting | AWS EC2 (Ubuntu 24.04), Docker, nginx, optional Let's Encrypt HTTPS |
| Data pipeline | Databricks, PySpark, pymongo, Delta Lake |

---

## Project structure

```
Ecom-website-mod/
├── server.js          # Express server, routes, MongoDB connection
├── userSchema.js      # Mongoose schema/model for submitted checkout data
├── package.json       # Dependencies and scripts
├── package-lock.json  # Locked dependency versions
├── dockerfile         # Instructions for building a Node container
├── products.xml       # XML-shaped product content (not used by app.js)
└── public/            # Files served to the browser by Express
    ├── index.html     # Storefront page and checkout form
    ├── style.css      # Page styles and responsive layout
    ├── app.js         # Product selection and checkout UI behavior
    └── Images/        # Product, logo, payment, and feature images
```

---

## How the website works

### Backend: `server.js`

**Setup**
- `require('dotenv').config()` loads `MONGO_URI` and `PORT` from `.env`.
- `express` is the web framework for routes and middleware.
- `mongoose` connects Node.js to MongoDB and defines models.
- `path` builds file paths that work on any OS.
- `require('./userSchema')` imports the Mongoose user model.

**Middleware**
- `express.json()` parses JSON request bodies into `req.body`.
- `express.urlencoded({ extended: true })` parses HTML form submissions into `req.body`.
- `express.static('public')` serves HTML, CSS and JS from the `public` folder.

**Database**
- `mongoose.connect(process.env.MONGO_URI)` connects to MongoDB. `.then()` logs success and `.catch()` logs the error.

**Routes**
- `GET /` sends `public/index.html`.
- `POST /post` saves the submitted data with `userModel.create(req.body)`. It returns `{ status: 'success' }`, or `{ error: message }` if validation or saving fails.

**Server**
- `PORT` comes from `.env` and defaults to `3000`. `app.listen(PORT)` starts the server.

### Schema: `userSchema.js`

Defines the fields and validations for each checkout submission (name, phone, address, card details) and is registered as the `users` model. It uses `{ timestamps: true }`, so every document gets `createdAt` and `updatedAt`. The Databricks pipeline uses these for incremental loading.

### Frontend: `public/`

- `index.html` defines the storefront and includes the CSS and JS. Its form has `action="/post"`, so the browser (not `app.js`) sends the checkout fields to the server.
- `style.css` styles the page using classes such as `.slider`, `.product` and `.payment`.
- `app.js` holds the sneaker data and click handlers. It changes the selected sneaker, price, image, colour and size, and opens and closes the checkout panel.
- `products.xml` is referenced by a script tag in the HTML, but the product list is actually defined in `app.js`. The XML file is not part of the active data flow.

### Request flow

```
Browser
  ├── GET /             → server.js sends public/index.html
  ├── Loads style.css   → styles index.html
  ├── Loads app.js      → updates product, colour, size, opens checkout panel
  └── Submits form: POST /post
        └── server.js parses fields
              └── userSchema.js validates via Mongoose
                    └── MongoDB stores a document in the users collection
```

---

## Run locally

Requirements: Node.js (LTS) and a MongoDB Atlas cluster.

```bash
git clone https://github.com/TANISH255/Ecom-website-mod.git
cd Ecom-website-mod
npm install
```

Create a `.env` file in the project root (no quotes, no spaces around `=`):

```
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/mydb?retryWrites=true&w=majority
PORT=3000
```

Start it:

```bash
node server.js
```

You should see `MongoDB connected` and `server started on 3000`. Open `http://localhost:3000`.

If the connection fails, check Atlas → **Network Access** and add your current IP. If your password contains special characters (`@`, `#`, `/`), URL-encode them or choose a password with letters and numbers only.

### Run with Docker

```bash
docker build -t ecom .
docker run -p 3000:3000 --env-file .env ecom
```

---

## Deploy on AWS EC2

### Step 1: Launch the instance

1. Open **EC2 → Launch instance** and name it `ecom-server`.
2. Choose **Ubuntu 24.04 LTS**.
3. Pick a type labelled **Free tier eligible**, usually `t3.micro`.
4. Create an **RSA `.pem` key pair** and download it.
5. Create a security group allowing **SSH (22) from My IP only**, plus **HTTP (80)** and **HTTPS (443)** from anywhere.
6. Set storage to **20 GB gp3** (the free allowance is 30 GB).
7. Click **Launch instance**.

### Step 2: Elastic IP

Keep one, but only while it is attached to a running instance. An unattached Elastic IP is never free.

1. Go to **EC2 → Elastic IPs → Allocate**, then **Actions → Associate** with your instance.
2. If you ever delete the instance, release the Elastic IP too.

Without it, the public IP changes on every stop and start and breaks your Atlas allowlist. The IP is called `X.X.X.X` below.

### Step 3: Atlas allowlist

In Atlas → **Network Access**, add `X.X.X.X/32`. Atlas M0 is free.

### Step 4: Connect and prepare the server

On Windows PowerShell, lock down the key file, then connect:

```powershell
icacls .\ecom-key.pem /inheritance:r
icacls .\ecom-key.pem /grant:r "$($env:USERNAME):(R)"
ssh -i .\ecom-key.pem ubuntu@X.X.X.X
```

On the server:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io git nginx
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
```

Add 1 GB of swap. A micro instance has only 1 GB of RAM, and `npm ci` or `docker build` can crash without swap:

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
exit
```

SSH back in so the `docker` group applies.

### Step 5: Code, `.env`, container

```bash
git clone https://github.com/TANISH255/Ecom-website-mod.git
cd Ecom-website-mod
nano .env            # MONGO_URI=... and PORT=3000
chmod 600 .env

docker build -t ecom .
docker run -d --name ecom --restart unless-stopped \
  -p 127.0.0.1:3000:3000 --env-file .env ecom
docker logs ecom     # expect "server started on 3000" and "MongoDB connected"
```

The container listens only on `127.0.0.1`, so the app is reachable from outside only through nginx.

### Step 6: nginx

Create `/etc/nginx/sites-available/ecom`:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/ecom /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Visit `http://X.X.X.X` and submit the form. A new document should appear in Atlas.

### Step 7: Free HTTPS (optional)

Skip Route 53 and buying a domain. Use a free subdomain from DuckDNS:

1. Sign in at [duckdns.org](https://www.duckdns.org), create a subdomain such as `tanish-shop`, and set its IP to `X.X.X.X`.
2. In the nginx config, change `server_name _;` to `server_name tanish-shop.duckdns.org;`, then reload nginx.
3. Run:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tanish-shop.duckdns.org
```

Let's Encrypt certificates are free and renew automatically.

### Updating the site later

```bash
cd Ecom-website-mod && git pull
docker build -t ecom .
docker rm -f ecom
docker run -d --name ecom --restart unless-stopped \
  -p 127.0.0.1:3000:3000 --env-file .env ecom
```

### Keeping it free

- **Stop the instance** when you are not using it (EC2 → Instance state → Stop). Stopped instances don't bill for compute, but the attached disk still counts toward the 30 GB storage allowance.
- **Elastic IP:** keep it only while attached to a *running* instance. If the instance is stopped for long, or deleted, release the IP.
- **Set a budget alert** in AWS Billing so any unexpected charge reaches you early.
- Free-tier terms change and differ by account, so check your own Billing page for what applies to you.
- **After a demo, close the website port.** The form accepts anonymous submissions, so remove the HTTP/HTTPS rules or stop the instance once you are done.
- Atlas M0 and Databricks Free Edition cost nothing, but check their current limits.

---

## Databricks pipeline

The notebook `Ecom_data_load` pulls new documents from Atlas and merges them into a Delta table. It is idempotent, so running it twice never creates duplicates.

### Steps

1. **Install libraries:** `%pip install pymongo dnspython` (in its own cell).
2. **Credentials:** the Atlas password is stored in a Databricks secret scope and read with `dbutils.secrets.get`. It is never written in the notebook.
3. **Connect:** build the URI with `quote_plus` so special characters in the password are escaped, then create a `MongoClient`.
4. **Explicit schema:** a Spark `StructType` avoids int/float inference problems from Mongo.
5. **Incremental filter:** read `max(createdAt)` from the Delta table and fetch only newer documents:
   ```python
   query = {}
   if spark.catalog.tableExists(TABLE):
       last = spark.sql(f"SELECT max(createdAt) AS m FROM {TABLE}").first()["m"]
       if last:
           query = {"createdAt": {"$gt": last}}
   ```
   MongoDB operators need the `$` prefix (`$gt`, not `gt`).
6. **Shape rows:** convert each document to a tuple in schema order (`_id` as a string, numbers cast with `int`).
7. **Load:**
   - First run: create the Delta table with `saveAsTable`.
   - Later runs: `MERGE` on `_id`, inserting new rows and updating only rows whose `updatedAt` is newer.
8. **Verify:** `DESCRIBE DETAIL`, `SELECT`, and `DESCRIBE HISTORY` on the table.

### Delta table: `users_bronze`

| Column | Type |
|---|---|
| `_id` | string |
| `name` | string |
| `phone` | long |
| `address` | string |
| `card` | string |
| `card_month` | int |
| `card_year` | int |
| `card_cvv` | int (dummy value) |
| `createdAt` | timestamp |
| `updatedAt` | timestamp |

### Scheduling

Create a Databricks **Job** with a Notebook task and a schedule (for example, hourly). Because the password comes from a secret scope, no cell needs interactive input.

### Atlas network access for Databricks

Databricks serverless compute has no fixed IP, so Atlas must allow connections from it. For this practice project that means adding `0.0.0.0/0` in Atlas → Network Access. That is acceptable only for a throwaway database with a strong password. Do not do this with real data.

---

## Security notes

- Credentials live in `.env` (website) and a Databricks secret scope (pipeline). `.env` is in `.gitignore` and must never be committed.
- If a password or connection string has ever appeared in a screenshot, chat, video or commit, rotate it (Atlas → Database Access → Edit user → Edit Password).
- Before publishing the demo video, make sure no frame shows the connection string, password, `.env`, or secret scope contents.
- `card_cvv`, `card_month` and `card_year` are stored only because this is a dummy checkout. A real site must never store a CVV (PCI DSS) and should hand card handling to a payment provider such as Stripe or Razorpay.

## Possible improvements

- Silver layer: clean types, remove duplicates, mask the phone number and address
- Gold layer: orders per product, once the form also saves the chosen product, size and price
- Filter on `updatedAt` instead of `createdAt` so edits made in Atlas are also captured
- Replace the form's card fields with a payment provider integration
- CI/CD: build and deploy to EC2 automatically on push

## Author

**Tanish** · [GitHub: TANISH255](https://github.com/TANISH255)
