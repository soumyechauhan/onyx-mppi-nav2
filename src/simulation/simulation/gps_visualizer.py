from collections import deque
from math import cos, isfinite, radians, sin, sqrt
import signal

import rclpy
from geometry_msgs.msg import Point
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import NavSatFix, NavSatStatus
from visualization_msgs.msg import Marker


WGS84_SEMI_MAJOR_AXIS = 6378137.0
WGS84_ECCENTRICITY_SQUARED = 6.69437999014e-3
MAX_TRAIL_POINTS = 2000


def geodetic_to_enu(latitude: float, longitude: float, altitude: float):
    """Convert GPS coordinates to ENU metres around the simulation's 0,0 datum."""
    lat = radians(latitude)
    lon = radians(longitude)
    sin_lat = sin(lat)
    prime_vertical_radius = WGS84_SEMI_MAJOR_AXIS / sqrt(
        1.0 - WGS84_ECCENTRICITY_SQUARED * sin_lat * sin_lat)

    ecef_x = (
        (prime_vertical_radius + altitude) * cos(lat) * cos(lon))
    ecef_y = (
        (prime_vertical_radius + altitude) * cos(lat) * sin(lon))
    ecef_z = (
        (prime_vertical_radius * (1.0 - WGS84_ECCENTRICITY_SQUARED)
         + altitude) * sin_lat)

    # The world datum is latitude 0, longitude 0, altitude 0.
    return ecef_y, ecef_z, ecef_x - WGS84_SEMI_MAJOR_AXIS


class GpsVisualizer(Node):
    def __init__(self):
        super().__init__('onyx_gps_visualizer')
        self.marker_publisher = self.create_publisher(
            Marker, '/gps/markers', 10)
        self.trail = deque(maxlen=MAX_TRAIL_POINTS)
        self.subscription = self.create_subscription(
            NavSatFix, '/gps/fix', self.on_gps_fix, 10)
        self.has_logged_fix = False

    def on_gps_fix(self, fix: NavSatFix):
        if fix.status.status < NavSatStatus.STATUS_FIX:
            self.get_logger().warning(
                f'GPS has no fix (status {fix.status.status}).')
            return

        coordinates = (fix.latitude, fix.longitude, fix.altitude)
        if not all(isfinite(value) for value in coordinates):
            self.get_logger().warning('Ignoring non-finite GPS coordinates.')
            return

        east, north, up = geodetic_to_enu(*coordinates)
        point = Point(x=east, y=north, z=up)
        self.trail.append(point)

        current = Marker()
        current.header.frame_id = 'odom'
        current.header.stamp = fix.header.stamp
        current.ns = 'gps'
        current.id = 0
        current.type = Marker.SPHERE
        current.action = Marker.ADD
        current.pose.position = point
        current.pose.orientation.w = 1.0
        current.scale.x = 0.2
        current.scale.y = 0.2
        current.scale.z = 0.2
        current.color.g = 1.0
        current.color.a = 1.0

        trail = Marker()
        trail.header = current.header
        trail.ns = 'gps'
        trail.id = 1
        trail.type = Marker.LINE_STRIP
        trail.action = Marker.ADD
        trail.points = list(self.trail)
        trail.scale.x = 0.04
        trail.color.r = 0.1
        trail.color.g = 0.6
        trail.color.b = 1.0
        trail.color.a = 1.0

        self.marker_publisher.publish(current)
        self.marker_publisher.publish(trail)

        if not self.has_logged_fix:
            self.get_logger().info(
                f'GPS fix visualized in odom at '
                f'({east:.2f}, {north:.2f}, {up:.2f}) m.')
            self.has_logged_fix = True


def main(args=None):
    rclpy.init(
        args=args,
        signal_handler_options=SignalHandlerOptions.NO,
    )
    node = GpsVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
