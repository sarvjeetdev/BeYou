# BeYou - Secure Social Media Platform

## 📌 Project Overview
BeYou is a **secure social media platform** designed for IIITD internal network deployment. This guide will help you **set up the project locally**, ensuring everything runs smoothly on your machine.

---
## 🚀 Getting Started

### 1️⃣ **Clone the Repository**
On your local machine, run:
```sh
git clone https://github.com/YOUR-REPO/BeYou.git
cd BeYou
```
---
### 2️⃣ **Install Dependencies**
Make sure **Docker** and **Docker Compose** are installed.

#### **🔹 Install Docker (if not installed)**
- **Ubuntu/Linux:**
  ```sh
  sudo apt update && sudo apt install docker.io -y
  sudo systemctl start docker
  sudo systemctl enable docker
  ```
- **Windows & Mac:** [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)

#### **🔹 Install Docker Compose**
Run:
```sh
sudo apt install docker-compose -y
```
Verify installation:
```sh
docker --version
docker-compose --version
```
---
### 3️⃣ **Set Up Environment Variables**
Copy the `.env.example` file and configure it:
```sh
cp backend/.env.example backend/.env
```
Modify `.env` based on local settings:
```sh
nano backend/.env
```
Save and exit.

---
### 4️⃣ **Start the Project Using Docker**
Run the following command from the project root (`BeYou/`):
```sh
docker-compose up -d --build
```
This will:
- Start **Django backend** (`backend`)
- Start **MongoDB database** (`db`)

To check running containers:
```sh
docker ps
```

---
### 5️⃣ **Access BeYou Locally**
Once the services are running:
- Open **http://192.168.2.239/** in your browser (adjust IP if needed).

If everything is set up correctly, you should see:
```
Hello, World! BeYou is running successfully.
```


### Copy Files from VM to Local Machine
Use this command from your local machine (Windows Command Prompt or PowerShell):

```
scp iiitd@192.168.2.239:/path/to/remote/file C:\path\to\local\destination
```


## 🎉 **You're All Set!**
Now you can access **BeYou** internally and securely. 🚀 Enjoy!

