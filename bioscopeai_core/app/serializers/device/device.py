from bioscopeai_core.app.models.device import Device
from bioscopeai_core.app.schemas.device import DeviceMinimalOut, DeviceOut


class DeviceSerializer:
    @staticmethod
    def device_to_out(device: Device) -> DeviceOut:
        return DeviceOut(
            id=device.id,
            name=device.name,
            hostname=device.hostname,
            location=device.location,
            firmware_version=device.firmware_version,
            is_online=device.is_online,
            last_seen=device.last_seen,
            registered_at=device.registered_at,
        )

    @staticmethod
    def device_to_out_list(devices: list[Device]) -> list[DeviceOut]:
        return [DeviceSerializer.device_to_out(device) for device in devices]

    @staticmethod
    def device_to_out_minimal(device: Device) -> DeviceMinimalOut:
        return DeviceMinimalOut(
            id=device.id,
            name=device.name,
        )


def get_device_serializer() -> DeviceSerializer:
    return DeviceSerializer()
