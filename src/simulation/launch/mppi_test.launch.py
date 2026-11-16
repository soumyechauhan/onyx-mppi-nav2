from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare, FindPackagePrefix

def generate_launch_description():

    # Our custom Gazebo world
    world = PathJoinSubstitution([
        FindPackageShare('simulation'),
        'worlds',
        'mppi_test_world.sdf'
    ])

    # Start Gazebo Fortress (version 6)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            ])
        ),
        launch_arguments={
            'gz_args': ['-r ', world],
            'gz_version': '6',
        }.items()
    )

    # Make Onyx meshes available to Gazebo
    resource_path = [
    PathJoinSubstitution([
        FindPackagePrefix('description'),
        'share'
    ]),
    ':',
    EnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        default_value=''
    )
]

    # Start robot_state_publisher
    robot_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('description'),
                'launch',
                'description.launch.py'
            ])
        ),
        launch_arguments={
            'use_sim_time': 'true'
        }.items()
    )

    # Spawn Onyx after Gazebo has started
    spawn_robot = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-world', 'mppi_test_world',
                    '-topic', 'robot_description',
                    '-name', 'onyx',
                ],
                output='screen'
            )
        ]
    )

    # Connect Gazebo clock to ROS
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
        ],
        output='screen'
    )

    # Connect movement, odometry, TF and joint states
    drive_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        output='screen'
    )
    lidar_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=[
        '/lidar/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'
    ],
    output='screen'
    )

    return LaunchDescription([
        SetEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            resource_path
        ),
        gazebo,
        robot_description,
        spawn_robot,
        clock_bridge,
        drive_bridge,
        lidar_bridge,
    ])

