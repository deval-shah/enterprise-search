# UI

The UI is an expiremental frontend application (boilerplate) built using Next.js 14 (app router) to interact with the Enterprise Search API. It is a chat interface for users to query over uploaded documents.

<div align="center">
  <img src="assets/demo.png" alt="LlamaSearch UI Demo" width="800" />
  <p>
    <em>Figure 1: LlamaSearch UI Interface (experimental)</em>
  </p>
</div>

## Table of Contents
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Getting Started](#-getting-started)
  - [Installation](#-installation)
  - [Running with Docker](#-running-with-docker)
  - [Running Locally](#-running-locally)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [License](#-license)

## Features

- 🚀 Built using Next.js 14 app router
- 🎨 Responsive design using Tailwind CSS
- 🔒 Secure authentication with Firebase
- 💬 Real-time chat interface with WebSocket streaming support
- 📁 File upload functionality
- 🌓 Dark mode support

## Prerequisites

Before you begin, ensure you have the following installed:
- [Node.js](https://nodejs.org/) (LTS version recommended)
- [npm](https://www.npmjs.com/) (comes with Node.js)
- [Docker](https://www.docker.com/) (optional, for containerized deployment)

## Getting Started

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

### Running with Docker

1. Build and run the Docker container:
   ```bash
   docker-compose up --build
   ```

2. Access the application at `http://localhost:3000`

3. To stop the application:
   ```bash
   docker-compose down
   ```

### Running Locally

1. Start the development server:
   ```bash
   npm run dev
   ```

2. Open your browser and navigate to `http://localhost:3000`

## Configuration

1. Copy the `.env.local.example` file to `.env.local`:
   ```bash
   cp .env.local.example .env.local
   ```

2. Update the `.env.local` file with your Firebase and API configurations.

### Firebase Setup

*Remember to use the same firebase project details used for the backend.*

To set up Firebase credentials in your `.env.local` file, follow these steps:

1. Go to the [Firebase Console](https://console.firebase.google.com/) and select your project (or create a new one).

2. Navigate to Project Settings (gear icon near the top left) > Service Accounts.

3. Click on "Generate new private key" to download a JSON file containing your Firebase Admin SDK credentials.

4. Open the downloaded JSON file and use its contents to fill in the following variables in your `.env.local` file:

   ```
   FIREBASE_ADMIN_CLIENT_EMAIL=your-client-email@your-project-id.iam.gserviceaccount.com
   FIREBASE_ADMIN_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour long private key here\n-----END PRIVATE KEY-----\n"
   ```

   Make sure to keep the quotes around the private key and replace newline characters with `\n`.

5. Set up the authentication cookie name and signature keys:

   ```
   AUTH_COOKIE_NAME=AuthToken
   AUTH_COOKIE_SIGNATURE_KEY_CURRENT=your-current-secret-key
   AUTH_COOKIE_SIGNATURE_KEY_PREVIOUS=your-previous-secret-key
   ```

   Generate strong, unique strings for both the current and previous signature keys.

6. Configure the security setting for cookies:

   ```
   USE_SECURE_COOKIES=false
   ```

   Set this to `true` in production environments.

7. Go to your Firebase project settings and find the "Your apps" section. Click on the web app (create one if you haven't already) and copy the configuration values to fill in these variables:

   ```
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
   NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
   NEXT_PUBLIC_FIREBASE_DATABASE_URL=https://your-project-id.firebaseio.com
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
   ```

8. Set the API URL for your backend:

   ```
   NEXT_PUBLIC_API_URL=http://localhost:8010
   ```

   Update this URL to match your backend's address in different environments.

Remember to never commit your `.env.local` file to version control as it contains sensitive information.

## Usage

1. Register a new account or log in with existing credentials.
2. Upload documents using the file upload feature.
3. Use the chat interface to interact with the LlamaSearch AI and analyze your documents.
4. Explore additional features like document management and user settings.

## 📄 License

This project is licensed under the *SOFTWARE LICENCE AGREEMENT* - see the [LICENSE](../LICENSE) file for details.

