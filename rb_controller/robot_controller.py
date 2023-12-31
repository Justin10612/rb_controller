import rclpy
import time
from rclpy.node import Node

from std_msgs.msg import String, Bool, Int32
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy


class RobotController(Node):
    # Parameter
    __FOLLOW_MODE_BTN = 1 #B
    __TELEOP_MODE_BTN = 0 #A
    __IDLE_MODE_BTN = 3 #y
    # Mode
    follow_btn_state = False
    teleop_btn_state = False
    idle_btn_state = False
    robot_state = 'IDLE'
    last_robot_state = 'IDLE'
    led_state = 0.0
    target_status = False
    # Button State
    follow_btn_flag = True
    teleop_btn_flag = True
    idle_btn_flag = True

    timer0 = 0
    timer1 = 0

    def __init__(self):
        super().__init__('robot_controller')
        # Create publisher
        self.idle_bool_pub_ = self.create_publisher(Bool, 'idle_bool', 10)
        self.robot_state_pub_ = self.create_publisher(String, 'robot_mode', 10)
        self.led_state_pub_ = self.create_publisher(Int32, 'led_state', 10)
        # Create subscriber
        self.joy_sub_ = self.create_subscription(Joy, 'joy', self.button_read, 10)
        self.joy_sub_  # prevent unused variable warning
        self.target_status_sub_ = self.create_subscription(Bool, 'target_status', self.target_status_read, 10)
        self.target_status_sub_  # prevent unused variable warning
        # Log Robot State
        self.get_logger().info('Robot State: "%s "' % self.robot_state)

    def button_read(self, joy_msg):
        # ############# Button Reading #############
        # Idle Mode Button
        if joy_msg.buttons[self.__IDLE_MODE_BTN] == 1 and self.idle_btn_flag :
            self.idle_btn_flag = False
            # self.get_logger().info('IDLE_btn_pressed')
            # Clear status
            self.idle_btn_state = True
        elif joy_msg.buttons[self.__IDLE_MODE_BTN] == 0 and not(self.idle_btn_flag):
            self.idle_btn_flag = True
        else:
            self.idle_btn_state = False
        
        # Follow Mode Button
        if joy_msg.buttons[self.__FOLLOW_MODE_BTN] == 1 and self.follow_btn_flag :
            self.follow_btn_flag = False
            # self.get_logger().info('Follow_btn_pressed')
            # Change State
            self.follow_btn_state = True
        elif joy_msg.buttons[self.__FOLLOW_MODE_BTN] == 0 and not(self.follow_btn_flag):
            self.follow_btn_flag = True
        else:
            self.follow_btn_state = False
        
        # Teleop Mode Button
        if joy_msg.buttons[self.__TELEOP_MODE_BTN] == 1 and self.teleop_btn_flag :
            self.teleop_btn_flag = False
            # self.get_logger().info('Teleop_btn_pressed')
            # Change State
            self.teleop_btn_state = True
        elif joy_msg.buttons[self.__TELEOP_MODE_BTN] == 0 and not(self.teleop_btn_flag):
            self.teleop_btn_flag = True
        else:
            self.teleop_btn_state = False

        ############## FSM ##############
        idle_msg = Bool()
        if self.robot_state=='IDLE' :
            # Mux Cut-off Output, Switch to E-STOP
            idle_msg.data = True
            self.led_state = 0
            # Switch to Follow Mode
            if self.follow_btn_state==True and self.target_status==True:
                self.robot_state = 'FOLLOW'
                self.led_state = 1
            # Switch to Teleoperating Mode
            if self.teleop_btn_state==True:
                self.robot_state = 'TELEOP'
                self.led_state = 2
        else:
            idle_msg.data = False
            # Set Start Time (To calculate the time of target lost)
            if self.robot_state == 'FOLLOW' and self.target_status == True:
                self.timer0 = round(time.time(), 0)
                self.timer1 = self.timer0 + 5.0
            # Target lost Time Count
            elif self.robot_state == 'FOLLOW' and self.target_status == False:
                if round(time.time(), 0) == self.timer1:
                    self.robot_state = 'IDLE'
                # self.get_logger().info('TIME count: "%f"' % (round(time.time(), 2)-self.timer0))
            # Go back to Idel Mode
            if self.idle_btn_state == True:
                self.robot_state = 'IDLE'

        # Publish Robot_state
        mode_msg = String()
        mode_msg.data = self.robot_state
        self.robot_state_pub_.publish(mode_msg)
        # Publish LED states
        led_msg = Int32()
        led_msg.data = self.led_state
        self.led_state_pub_.publish(led_msg)
        # Publish Idle message
        self.idle_bool_pub_.publish(idle_msg)
        # Log Robot_state
        if (self.last_robot_state != self.robot_state):
            self.get_logger().info('Robot State: "%s "' % self.robot_state)
        self.last_robot_state = self.robot_state

    def target_status_read(self, msg):
        self.target_status = msg.data
        # self.get_logger().info('Target_status: %b ' % self.target_status)

def main(args=None):
    rclpy.init(args=args)
    robot_controller = RobotController()
    rclpy.spin(robot_controller)
    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    robot_controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()