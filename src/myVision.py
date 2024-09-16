from datetime import datetime, timezone
import time
from typing import Any, ClassVar, Dict, Mapping, Optional, Sequence, cast, List
from viam.utils import ValueTypes
from typing_extensions import Self
from viam.services.vision import Vision, CaptureAllResult
from viam.logging import getLogger
from viam.proto.app.robot import ComponentConfig
from viam.proto.service.vision import Classification, Detection, GetPropertiesResponse
from viam.proto.common import ResourceName, PointCloudObject
from viam.resource.base import ResourceBase
from viam.resource.types import Model, ModelFamily
from viam.components.camera import Camera, ViamImage
from viam.media.utils.pil import viam_to_pil_image
from viam.utils import struct_to_dict, from_dm_from_extra
from viam.errors import NoCaptureToStoreError


LOGGER = getLogger(__name__)

class MyVision(Vision):
    MODEL: ClassVar[Model] = Model(ModelFamily("bill", "vision"), "fall")
    
    def __init__(self, name: str):
        super().__init__(name)

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        # Create a new instance of MyVision and configure it
        vision = cls(config.name)
        vision.reconfigure(config, dependencies)
        return vision

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Sequence[str]:
        return []

    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        LOGGER.info("Reconfiguring " + self.name)
        self.config = config
        self.DEPS = dependencies
        config_dict = struct_to_dict(config.attributes)
        self.base_vision_name = config_dict["base_vision_name"]
        self.valid_labels = config_dict["valid_labels"]
        self.label_confidence = config_dict["label_confidence"]
        pass

    async def get_cam_image(
        self,
        camera_name: str
    ) -> ViamImage:
        actual_cam = self.DEPS[Camera.get_resource_name(camera_name)]
        cam = cast(Camera, actual_cam)
        cam_image = await cam.get_image(mime_type="image/jpeg")
        return cam_image

    async def get_model_detection(
        self,
        vision_name: str,
        img: ViamImage
    ) -> Detection:
        actual_model = self.DEPS[Vision.get_resource_name(vision_name)]
        vision = cast(Vision, actual_model)
        detections = await vision.get_detections(img)
        
        # Filter detections based on valid labels
        filtered_detections = [d for d in detections if d.class_name in self.valid_labels]

        # Ensure that detections is returned
        return filtered_detections

    async def get_detections_from_camera(
        self, camera_name: str, *, extra: Optional[Mapping[str, Any]] = None, timeout: Optional[float] = None
    ) -> List[Detection]:
        return await self.get_model_detection(self.base_vision_name, await self.get_cam_image(camera_name))
 
    async def get_detections(
        self,
        image: ViamImage,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> List[Detection]:
        return await self.get_model_detection(self.base_vision_name, image)
    
    async def get_classifications_from_camera(
        self,
        camera_name: str,
        count: int,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> List[Classification]:
        return await self.get_classifications(await self.get_cam_image(camera_name))

    
    async def get_classifications(
        self,
        image: ViamImage,
        count: int,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> List[Classification]:
        classifications = []
        # Await the coroutine to get the detections list
        detections = await self.get_detections(image)

        # Check if detections is None or empty
        if detections is None:
            # Log or handle the case when no detections are returned
            return classifications  # Return an empty list

        for detection in detections:
            if detection.class_name in self.valid_labels and detection.confidence >= self.label_confidence:
                # Extract the bounding box coordinates from the Viam detection
                x_min = detection.x_min
                y_min = detection.y_min
                x_max = detection.x_max
                y_max = detection.y_max
                confidence = detection.confidence
                class_detect = detection.class_name

                # Calculate height and width of the bounding box
                height = y_max - y_min
                width = x_max - x_min

                # Create a Classification object based on bounding box dimensions
                classification = Classification()
                classification.confidence = confidence
                classification.class_name = 'No fall' if height > width else 'Fall'
                
                # Add the Classification object to the list
                classifications.append(classification)

        return classifications


    
    async def get_object_point_clouds(
        self, camera_name: str, *, extra: Optional[Mapping[str, Any]] = None, timeout: Optional[float] = None
    ) -> List[PointCloudObject]:
        return
    
    async def do_command(self, command: Mapping[str, ValueTypes], *, timeout: Optional[float] = None) -> Mapping[str, ValueTypes]:
        return

    async def capture_all_from_camera(
        self,
        camera_name: str,
        return_image: bool = False,
        return_classifications: bool = False,
        return_detections: bool = False,
        return_object_point_clouds: bool = False,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> CaptureAllResult:
        result = CaptureAllResult()
        result.image = await self.get_cam_image(camera_name)
        result.detections = await self.get_detections(result.image)
        result.classifications = await self.get_classifications(result.image, 1)
        LOGGER.info("capture_all_from_camera is called")
        # Check if the call is from the data manager
        if from_dm_from_extra(extra):
            LOGGER.info("capture_all_from_camera is called from dm")
            # Check for classifications of type "Fall"
            has_fall_classification = any(
                classification.class_name == "Fall" for classification in result.classifications
            )
            
            # Raise NoCaptureToStoreError if no "Fall" classification is found
            if not has_fall_classification:
                raise NoCaptureToStoreError
            LOGGER.info("Fall seen")
        return result

    async def get_properties(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> GetPropertiesResponse:
        return GetPropertiesResponse(
            classifications_supported=True,
            detections_supported=True,
            object_point_clouds_supported=False
        )