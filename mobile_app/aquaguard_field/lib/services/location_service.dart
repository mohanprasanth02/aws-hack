import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';

class LocationService {
  // SNS College of Technology Campus center in Coimbatore default
  static const LatLng defaultCampusCoords = LatLng(11.1018, 77.0275);

  static Future<LatLng> getCurrentLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        return defaultCampusCoords;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          return defaultCampusCoords;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        return defaultCampusCoords;
      }

      Position pos = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 4),
      );

      return LatLng(pos.latitude, pos.longitude);
    } catch (e) {
      return defaultCampusCoords;
    }
  }

  // Calculate distance in meters between user and risk meter
  static double calculateDistanceMeters(LatLng start, LatLng end) {
    return Geolocator.distanceBetween(
      start.latitude,
      start.longitude,
      end.latitude,
      end.longitude,
    );
  }
}
