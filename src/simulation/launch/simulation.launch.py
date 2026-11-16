from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable,
    TimerAction)
from launch.conditions import UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution,
    PythonExpression)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackagePrefix, FindPackageShare


def generate_launch_description():
    world = PathJoinSubstitution([
        FindPackageShare('simulation'), 'worlds', 'tekno_world.sdf'])

    gz_flags = PythonExpression([
        "'-r -s ' if '", LaunchConfiguration('headless'),
        "' == 'true' else '-r '"])

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])),
        launch_arguments={
            'gz_args': [gz_flags, world],
            'gz_version': '8',
        }.items(),
    )

    description_root = PathJoinSubstitution([
        FindPackagePrefix('description'), 'share'])
    resource_path = [
        description_root,
        ':',
        EnvironmentVariable('GZ_SIM_RESOURCE_PATH', default_value=''),
    ]

    spawn_robot = TimerAction(
        period=5.0,
        actions=[Node(
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-world', 'tekno_world',
                '-topic', 'robot_description',
                '-name', 'onyx',
            ],
            output='screen',
        )],
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen',
    )

    sensor_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/gps/fix@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat',
            '/imu/data@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/lidar/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/front_cam/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/front_cam/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/rear_cam/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/rear_cam/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/aiming_cam/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/aiming_cam/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        output='screen',
    )

    drive_command_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        ],
        output='screen',
    )

    turret_command_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/turret/yaw/cmd@std_msgs/msg/Float64]gz.msgs.Double',
            '/turret/pitch/cmd@std_msgs/msg/Float64]gz.msgs.Double',
        ],
        output='screen',
    )

    gps_visualizer = Node(
        package='simulation',
        executable='onyx_gps_visualizer',
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=[
            '-d',
            PathJoinSubstitution([
                FindPackageShare('simulation'), 'rviz', 'onyx_lidar.rviz']),
        ],
        parameters=[{'use_sim_time': True}],
        condition=UnlessCondition(LaunchConfiguration('headless')),
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='true = no window (use for training).'),
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', resource_path),
        gz_sim,
        spawn_robot,
        clock_bridge,
        sensor_bridge,
        drive_command_bridge,
        turret_command_bridge,
        gps_visualizer,
        rviz,
    ])
