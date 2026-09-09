# IoT-Enabled Intelligent Environmental Control System for Mushroom Cultivation

An IoT and AI-based environmental control system developed to monitor and automatically regulate environmental conditions for mushroom cultivation.

## 📌 Project Overview

Mushroom cultivation requires controlled environmental conditions such as temperature, humidity, CO₂ concentration, soil moisture, and light intensity.

Traditional mushroom cultivation often relies on manual monitoring and control, which can be time-consuming and may result in unstable environmental conditions.

This project integrates:

- Internet of Things (IoT)
- Environmental sensors
- Raspberry Pi 4
- Machine Learning
- Firebase Realtime Database
- Web-based dashboard
- Automated misting control

The system collects real-time environmental data and uses a machine learning model to predict whether the misting system should be turned ON or OFF.

---

## 🎯 Aim

To design and implement an intelligent environmental control system for mushroom cultivation by integrating IoT-based sensing with AI-driven decision-making to optimize growth conditions and enhance productivity.

---

## 🎯 Objectives

1. Identify suitable AI methods for intelligent environmental control and determine key environmental parameters for mushroom cultivation.

2. Develop an IoT-enabled intelligent control system that integrates real-time sensor data with AI-based decision-making for automatic environmental regulation.

3. Evaluate the system in terms of prediction accuracy, resource efficiency, mushroom yield, and quality.

---

## 🏗️ System Architecture

The system consists of four main layers:

```text
┌─────────────────────────────┐
│       Sensing Layer         │
│                             │
│  DHT22                      │
│  MH-Z19B                    │
│  Capacitive Soil Moisture   │
│  TSL2591                    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         Edge Layer          │
│                             │
│       Raspberry Pi 4        │
│                             │
│ • Sensor data processing    │
│ • ML inference              │
│ • Control logic             │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         Cloud Layer         │
│                             │
│    Firebase Realtime DB     │
│                             │
│ • Store sensor readings     │
│ • Real-time synchronization │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      Application Layer      │
│                             │
│       Web Dashboard         │
│                             │
│ • Live monitoring           │
│ • Historical trends         │
│ • Misting control           │
└─────────────────────────────┘
