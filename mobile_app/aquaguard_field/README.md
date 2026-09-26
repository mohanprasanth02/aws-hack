# AquaGuard Field — Technician Mobile Companion App (Flutter)

A cross-platform Flutter mobile application designed for campus water maintenance technicians. Directly connects to the **AquaGuard AI Web Core** in real time.

---

## 🚀 Key Features

1. **Real-Time Task Feed**: Instant notification and synchronized queue of active leak dispatches, prioritized by AI anomaly severity (`Emergency`, `High`, `Medium`).
2. **Campus GPS Turn-by-Turn Routing**:
   - Interactive map displaying the technician's live GPS position alongside the target meter / facility at SNS College campus.
   - Dynamic polyline route with distance in meters/km and walk ETA.
   - One-tap intent to launch external Google Maps walking navigation.
3. **In-App Camera & Instant Proof-of-Work Sync**:
   - Technician photographs the repaired pipe, valve, or sub-meter on site.
   - Form for diagnosis notes and corrective action taken.
   - Multipart photo upload directly syncs to the central web application, rendering in the Work Load lightbox and automatically closing the linked anomaly.

---

## 🛠️ How to Run

### 1. Prerequisites
- [Flutter SDK](https://flutter.dev/docs/get-started/install) (v3.0.0 or higher)
- Android Studio / Xcode or VS Code with Flutter extension

### 2. Configure Host IP
Open [`lib/config/api_config.dart`](lib/config/api_config.dart):
- **Current Mobile Hotspot / Network IP**: `http://10.181.231.10:5000` (Configured as default).
- **Flutter Web Server**: `http://10.181.231.10:5050`
- **Android Emulator**: Uses `http://10.0.2.2:5000` (available via quick preset).

### 3. Install Dependencies & Launch
```bash
cd mobile_app/aquaguard_field
flutter pub get
flutter run
```

### 4. Technician Credentials
- **Email**: `worker@aquaguard.io`
- **Password**: `Worker123!`
