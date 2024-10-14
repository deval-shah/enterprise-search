# Interactive UI for Enterprise Search API

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Running with Docker](#running-with-docker)
  - [Running Locally](#running-locally)
- [Configuration](#configuration)
- [Usage](#usage)
- [License](#license)

## Overview

The UI is an expiremental frontend application built with Next.js 14 for the Enterprise Search project. It provides an interactive interface for users to interact with the Enterprise Search backend to query over uploaded documents.

## Features

- 🚀 Built using Next.js 14 app router
- 🎨 Responsive design using Tailwind CSS
- 🔒 Secure authentication with Firebase
- 💬 Real-time chat interface with WebSocket support
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

## Usage

1. Register a new account or log in with existing credentials.
2. Upload documents using the file upload feature.
3. Use the chat interface to interact with the LlamaSearch AI and analyze your documents.
4. Explore additional features like document management and user settings.

## 📄 License

This project is licensed under the *SOFTWARE LICENCE AGREEMENT* - see the [LICENSE](../LICENSE) file for details.