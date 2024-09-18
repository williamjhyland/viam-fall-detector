# viam-fall-detector

## Description

This project demonstrates the implementation of a custom Viam Vision service designed to detect fall events using existing camera detections. The vision service operates by analyzing the bounding boxes of detected objects in the camera's field of view. If a detection box has a valid class name, meets a minimum confidence threshold, and is wider than it is tall, the service classifies the detection as a "Fall." Conversely, if the bounding box is taller than it is wide, it is classified as "No Fall." This approach is ideal for applications that require monitoring for falls in real-time using an existing camera and detection setup.

## Viam Module

A module is a package with streamlined deployment to a Viam server. Modules can run alongside viam-server as separate processes, communicating with viam-server over UNIX sockets. A Viam Module can deploy and manage components such as a Viam Sensor.

## Viam Vision Service

The Viam Vision service enables a machine to use its onboard cameras to intelligently interpret the world. In this project, the vision service is configured to work with an existing person detection model or other detection sources to analyze bounding boxes for fall detection. This setup is particularly useful for monitoring environments where fall events need to be detected and handled promptly.

## Viam Vision Service Implementation

This custom vision service relies on detections provided by an existing vision service (e.g., a person detector). It uses these detections to classify objects into two categories: "Fall" and "No Fall." By leveraging Viam's Vision component, the service interacts with cameras and the vision service to process images, returning classifications based on the dimensions of detected bounding boxes.

## Configuration

To use this custom Viam Camera component, the following configuration is required:

Generalized Attribute Guide
```json
{
  "base_vision_name": "base_vision_name_here",
  "valid_labels": [
    "valid_label_here"
  ],
  "label_confidence": 0.0
}
```

Generic Example
```json
{
  "base_vision_name": "myPersonVision",
  "valid_labels": [
    "Person"
  ],
  "label_confidence": 0.3
}
```

This configuration specifies the existing vision service (base_vision_name) that provides detections, a list of valid labels (valid_labels) to filter the detections (e.g., "Person"), and the minimum confidence threshold (label_confidence) for a detection to be considered.

## Key Methods

- get_detections_from_camera: Retrieves detections from the specified camera using the existing vision service. Filters the detections based on valid labels and confidence, then classifies them as "Fall" or "No Fall" based on the bounding box dimensions.
- get_detections: Similar to get_detections_from_camera, but operates on a given image instead of fetching it from a camera.
- get_classifications_from_camera: Returns classifications for the objects detected in the camera's field of view. It uses the dimensions of bounding boxes to classify detections into "Fall" or "No Fall."
- get_classifications: Works like get_classifications_from_camera but operates on a given image.
- capture_all_from_camera: Captures all relevant data (image, detections, classifications) from the specified camera in one call.

This component offers a versatile solution for scenarios where a simulated video feed is necessary, such as in testing environments or controlled experiments.
