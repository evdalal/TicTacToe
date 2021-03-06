#!/usr/bin/env python

import cv2
import rospy
import argparse
import imutils
import time
import sys
import numpy as np
from collections import deque
from imutils.video import VideoStream
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
# Echo client program
import socket
import math
from text_to_speech import talk

#text to speech init
#engine = pyttsx.init()
#engine.setProperty('rate', 120)
#engine.setProperty('volume', 1)

start_of_game = True
frame_count = 0
frame_count_check = 0
pickup_place_counter = -1
square1, square2, square3, square4, square5, square6, square7, square8, square9 = 0,0,0,0,0,0,0,0,0
utterance_counter = -1
break_var = False
prev_board = [0,0,0,0,0,0,0,0,0] #previous board
f= open("/home/sar/catkin_ws/src/skill_assessment/TicTacToe/nodes/tictactoe/pieces_on_board.txt","w+") #makes comments on file to locate where it is in code

HOST = "192.168.1.115" # The UR IP address
PORT = 30002 # UR secondary client
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))


#changes degrees for robot joint to radians for each square of tic tac toe board
def degrees_to_radians(square_num):
	robot_position = {
"square1":{
	"base": 50.95,
	"shoulder": -108.82,
	"elbow": -122,
	"wrist1": -40.78,
	"wrist2": 95.82,
	"wrist3": 228.28
},
"square2":{
	"base": 61.53,
	"shoulder": -120.25,
	"elbow": -103.61,
	"wrist1": -45.53,
	"wrist2": 93.78,
	"wrist3": 243.12
},
"square3":{
	"base": 67.02,
	"shoulder": -134.11,
	"elbow": -77.76,
	"wrist1": -58.38,
	"wrist2": 91.65,
	"wrist3": 248.05
},
"square4":{
	"base": 42.1,
	"shoulder": -118.68,
	"elbow": -106.23,
	"wrist1": -44.34,
	"wrist2": 93.29,
	"wrist3": 225.68
},
"square5":{
	"base": 50.68,
	"shoulder": -127.48,
	"elbow": -90.8,
	"wrist1": -49.87,
	"wrist2": 95.84,
	"wrist3": 233.38
},
"square6":{
	"base": 58.41,
	"shoulder": -141.35,
	"elbow": -64.5,
	"wrist1": -61.58,
	"wrist2": 93.27,
	"wrist3": 242.5
},
"square7":{
	"base": 37.47,
	"shoulder": -129.83,
	"elbow": -84.8,
	"wrist1": -56.22,
	"wrist2": 86.94,
	"wrist3": 222.52
},
"square8":{
	"base": 43,
	"shoulder": -140.01,
	"elbow": -66.75,
	"wrist1": -61.97,
	"wrist2": 96.03,
	"wrist3": 224.19
},
"square9":{
	"base": 52.08,
	"shoulder": -149.57,
	"elbow": -49.68,
	"wrist1": -61.62,
	"wrist2": 88.88,
	"wrist3": 238.75
},
"top":{
	"base": 85.55,
	"shoulder": -82.85,
	"elbow": -107.1,
	"wrist1": -71.3,
	"wrist2": 93.65,
	"wrist3": 270.02
},

"out1":{
	"base": 85.76,
	"shoulder": -108.66,
	"elbow": -123.61,
	"wrist1": -36.65,
	"wrist2": 94.04,
	"wrist3": 267.67
},
"out2":{
	"base": 71.25,
	"shoulder": -102.37,
	"elbow": -132.02,
	"wrist1": -36.68,
	"wrist2": 94.02,
	"wrist3": 253.59
},
"out3":{
	"base": 72.77,
	"shoulder": -112.58,
	"elbow": -117.32,
	"wrist1": -38.45,
	"wrist2": 95.45,
	"wrist3": 254.78
},
"out4":{
	"base": 84.82,
	"shoulder": -97.30,
	"elbow": -139.65,
	"wrist1": -32.66,
	"wrist2": 95.42,
	"wrist3": 266.29
},
}
	b = robot_position[str(square_num)]["base"]
	s = robot_position[str(square_num)]["shoulder"]
	e = robot_position[str(square_num)]["elbow"]
	w1 = robot_position[str(square_num)]["wrist1"]
	w2 = robot_position[str(square_num)]["wrist2"]
	w3 = robot_position[str(square_num)]["wrist3"]
	base = b/180.0* math.pi
	shoulder = s/180.0* math.pi
	elbow = e/180.0* math.pi
	wrist1 = w1/180.0* math.pi
	wrist2 = w2/180.0* math.pi
	wrist3 = w3/180.0* math.pi
	return "[" + str(base) + "," + str(shoulder) + "," + str(elbow) + "," + str(wrist1) + "," + str(wrist2) + "," + str(wrist3) + "]"

#move robot to certain position	
def move_robot_j(pose):
	s.send("movej(" + pose + ", a=0.2, v=0.2)" + "\n")

def import_gripper_commands(f):
	l = f.read(1024)
	while (l):
		s.send(l)
		l = f.read(1024)

#must activate gripper before using open and close commands
def activate_gripper():
	f = open ("/home/sar/catkin_ws/src/skill_assessment/TicTacToe/nodes/test.script", "rb")
	import_gripper_commands(f)
	s.send("rq_activate_and_wait()" + "\n")
	s.send("end" + "\n")
	f.close()

def open_gripper():
	f = open ("/home/sar/catkin_ws/src/skill_assessment/TicTacToe/nodes/test.script", "rb")
	import_gripper_commands(f)
	s.send("rq_open()" + "\n")
	s.send("end" + "\n")
	f.close()
	
	
def close_gripper():
	f = open ("/home/sar/catkin_ws/src/skill_assessment//TicTacToe/nodes/test.script", "rb")
	import_gripper_commands(f)
	s.send("rq_close()" + "\n")
	s.send("end" + "\n")
	f.close()
	
def deactivate_gripper():
	s.send("end" + "\n")











#detects green board and finds center of image using green pixels
def find_center(image):
#image = cv2.imread(" frame " ) # --not sure if needed for camera
	rows, cols, channels = image.shape #width and height

	lower_green = np.array([40, 50, 10])
	upper_green = np.array([120, 150, 80]) #edit color values as necessary for camera, make large range in case lighting changes
	green = cv2.inRange(image, lower_green, upper_green)
	row_list = []
	col_list = []
	total_row = 0
	total_col = 0


	for i in range(0,rows): #collect pixels to find average, add to list
		for j in range(0,cols):
			k = green[i,j]
			if k == 255:
				row_list.append(i)
				col_list.append(j)

#calculates center row
	for x in row_list:
		total_row += x
	avg_row = total_row/(len(row_list))


#calculates center col
	for y in col_list:
		total_col += y
	avg_col = total_col/(len(col_list))
	return [avg_row, avg_col]

#finds top left corner and bottom right corner height and width
def get_upper_and_lower(expansion_size, row_addition, col_addition, avg_row, avg_col,img): #gets coordinates for each square for top and bottom corners
	middle_row = avg_row + row_addition #can be negative
	middle_col = avg_col + col_addition
#	for x in range(0, expansion_size):
#		for y in range(0, expansion_size+10):
#			img[middle_row+x, middle_col+y] = [0,0,255]
#			img[middle_row-x, middle_col+y] = [0,0,255]
#			img[middle_row-x, middle_col-y] = [0,0,255]
#			img[middle_row+x, middle_col-y] = [0,0,255]
	lower_corner_height, lower_corner_width = middle_row+expansion_size, middle_col+expansion_size+10
	upper_corner_height, upper_corner_width = middle_row-expansion_size, middle_col-expansion_size-10
	return [lower_corner_height, lower_corner_width, upper_corner_height, upper_corner_width]

#finds corners for each square
def find_range_for_all_squares(image):
	avg_row = find_center(image)[0]
	avg_col = find_center(image)[1]

	sq1 = get_upper_and_lower(40, -110, -130, avg_row, avg_col,image)
	sq2 = get_upper_and_lower(40, -110, 0, avg_row, avg_col,image)
	sq3 = get_upper_and_lower(40, -110, 130, avg_row, avg_col,image)
	sq4 = get_upper_and_lower(40, 0, -130, avg_row, avg_col,image)
	sq5 = get_upper_and_lower(40, 0, 0, avg_row, avg_col,image)
	sq6 = get_upper_and_lower(40, 0, 130, avg_row, avg_col,image)
	sq7 = get_upper_and_lower(40, 110, -140, avg_row, avg_col,image)
	sq8 = get_upper_and_lower(40, 110, 0, avg_row, avg_col,image)
	sq9 = get_upper_and_lower(40, 110, 130, avg_row, avg_col,image)
#	f.write("this is each square upper and lower coordinates and should be a list: {}\n".format([sq1, sq2, sq3, sq4, sq5, sq6, sq7, sq8, sq9]))
	return [sq1, sq2, sq3, sq4, sq5, sq6, sq7, sq8, sq9]
#	return image

#adds player's piece to list containing board elements after a certain number of frames (4)
def add_player_to_board_list(blue_list, dup_board, board):
#	dup_board = board
	global break_var
	global prev_board
	break_var = True
	for x in range(0,9):
		if dup_board[x] == 2:
			f.write("dup board is being changed from {} ".format(dup_board))
			dup_board[x] = 0
			f.write(" to this {} \n".format(dup_board))
		if prev_board[x] == 2:
			f.write("prev board is being changed from {} ".format(prev_board))
			prev_board[x] = 0
			f.write(" to this {} \n".format(prev_board))
	for x in range(0,9):
		if blue_list[x] > 700: 
			dup_board[x] = 1
		else:
			dup_board[x] = 0
	#makes sure that if someone's hand get in in a previous frame, dup_board is changed to how it should be

	if dup_board != prev_board:
		f.write("This is dup board: {} and prev board: {} \n".format(dup_board, prev_board))
		global frame_count
		frame_count += 1
		global frame_count_check
		#adds player to board after 4 frames, frames are slow so this slows the program a bit
		if frame_count == frame_count_check +3:
			frame_count_check = frame_count
			f.write("This is the frame_count_check: {} and frame count: {} \n".format(frame_count_check, frame_count))
			for x in range(0,9):
				if blue_list[x] > 400:
					board[x] = 1
					dup_board = list(board)
					prev_board = list(board)
					f.write("This is the new board after something was added: {}\n".format(board))
					break_var = False
#				else:
#					if board[x] != 2:
#						board[x] = 0
			f.write("This is the final board: {}\n".format(board))
		else:
			break_var = True

	f.write("This is the state of the board: {}\n".format(board))

#detects each square for each frame (in the future, each square can be detected at the beginning of the game and stored as a variable)
def detect_player_piece(player_blue_list, image, dup_board, board):
#	global frame_count
#	f.write("This is the frame count before being added: {}\n".format(frame_count))
#	frame_count += 1
#	f.write("This is the frame count AFTER being added: {}\n".format(frame_count))
#	f.write("This is frame count: {}\n".format(frame_count))
	global square1
	global square2
	global square3
	global square4
	global square5
	global square6
	global square7
	global square8
	global square9
#	f.write("These are the square coordinates, {},{},{},{},{},{},{},{}\n".format(square1, square2, square3, square4, square5, square6, square7, square8, square9))

#	if frame_count <= 1:
#		f.write("iterating through defining the squares\n")
	square_list = find_range_for_all_squares(image)
#		num1 = find_range_for_all_squares(image)[0][1]
#		f.write("This is what is returned: {}\n".format(num1))
	square1 = image[square_list[0][2]:square_list[0][0], square_list[0][3]:square_list[0][1]]
#		f.write("This is square one coordinates: {}\n".format(str(square1)))

	square2 = image[square_list[1][2]:square_list[1][0], square_list[1][3]:square_list[1][1]]

	square3 = image[square_list[2][2]:square_list[2][0], square_list[2][3]:square_list[2][1]]

	square4 = image[square_list[3][2]:square_list[3][0], square_list[3][3]:square_list[3][1]]

	square5 = image[square_list[4][2]:square_list[4][0], square_list[4][3]:square_list[4][1]]

	square6 = image[square_list[5][2]:square_list[5][0], square_list[5][3]:square_list[5][1]]

	square7 = image[square_list[6][2]:square_list[6][0], square_list[6][3]:square_list[6][1]]

	square8 = image[square_list[7][2]:square_list[7][0], square_list[7][3]:square_list[7][1]]

	square9 = image[square_list[8][2]:square_list[8][0], square_list[8][3]:square_list[8][1]]


# bgr values to detect blue
#	lower_blue = np.array([200,150,0])
#	upper_blue = np.array([255,240,100])
	lower_blue = np.array([150,50,0])
	upper_blue = np.array([255,240,140])

#assigning variable to number of blue pixels in each square
	blue1 = cv2.inRange(square1, lower_blue, upper_blue)
	blue2 = cv2.inRange(square2, lower_blue, upper_blue)
	blue3 = cv2.inRange(square3, lower_blue, upper_blue)
	blue4 = cv2.inRange(square4, lower_blue, upper_blue)
	blue5 = cv2.inRange(square5, lower_blue, upper_blue)
	blue6 = cv2.inRange(square6, lower_blue, upper_blue)
	blue7 = cv2.inRange(square7, lower_blue, upper_blue)
	blue8 = cv2.inRange(square8, lower_blue, upper_blue)
	blue9 = cv2.inRange(square9, lower_blue, upper_blue)

#list of number of blue pixels in each square
	player_blue_list[0] = np.sum(blue1>0)
#	f.write("This is the blue pixels in the first square: {}\n".format(player_blue_list[0]))
	player_blue_list[1] = np.sum(blue2>0)
	player_blue_list[2] = np.sum(blue3>0)
	player_blue_list[3] = np.sum(blue4>0)
	player_blue_list[4] = np.sum(blue5>0)
	player_blue_list[5] = np.sum(blue6>0)
	player_blue_list[6] = np.sum(blue7>0)
	player_blue_list[7] = np.sum(blue8>0)
	player_blue_list[8] = np.sum(blue9>0)
#	f.write("This is the player_blue list: {}\n".format(player_blue_list))
	add_player_to_board_list(player_blue_list, dup_board, board) 
#	f.write("this is on the board: {}\n".format(board))

#sees if certain spots on board equate to winning
def has_won(x,y,z,bo):
	if (bo[x] == 1) and (bo[y] == 1) and (bo[z] == 1):
		return 1
#playerwon
	elif (bo[x] == 2) and (bo[y] == 2) and (bo[z] == 2):
		return 2
#compwon
	else:
		return 3 #game not done

#uses has_won function for every single way to win on board
def has_won_all(b):
	if (has_won(0,1,2,b)==2) or (has_won(0,4,8,b)==2) or (has_won(0,3,6,b)==2) or (has_won(1,4,7,b)==2) or (has_won(2,5,8,b)==2) or (has_won(2,4,6,b)==2) or (has_won(3,4,5,b)==2) or (has_won(6,7,8,b)==2):
		#comp won
		return 2
	elif (has_won(0,1,2,b)==1) or (has_won(0,4,8,b)==1) or (has_won(0,3,6,b)==1) or (has_won(1,4,7,b)==1) or (has_won(2,5,8,b)==1) or (has_won(2,4,6,b)==1) or (has_won(3,4,5,b)==1) or (has_won(6,7,8,b)==1):
		#player won
		return 1
	else:
		#no one won, game not done, only know if tie is all spots on board are filled, not only if 3 is returned
		return 3

#iterates through each empty spot on board and sees if player will win with next move; if so, robot puts its piece on that piece
def block_player(board):
	ind = 10
	dup_list = board
	for t in range(0,9):
		if dup_list[t] == 0:
			dup_list[t] = 1
			if has_won_all(board) == 1:
				#print("This is the winning block for the player", t)
				ind = t
				break
			else:
				dup_list[t] = 0
	return ind


#iterates through each empty spot and sees if robot can win on next move
def cpu_winning_move(board):
	ind = 10
	dup_list2 = board
	for t in range(0,9):
		if dup_list2[t] == 0:
			dup_list2[t] = 2
			if has_won_all(board) == 2:
				ind = t
				break
			else:
				dup_list2[t] = 0
	return ind


#if cannot win or block player, checks for corner pieces, then center, then remaining spots between corners
def select_square(board): #last option after blocking player and winning is not possible
	i = 0
	for l in range(0,9):
		if l in [0,2,6,8]:#checks for corner pieces first
			if board[l] == 0: #makes sure space is open
				i = l
				break
			else:
				continue
	if i not in [0,2,6,8]: #checks for center
		if board[4] == 0: #makes sure space is open
			i = 4
		elif i not in [0,2,4,6,8]:#checking for sides
			for l in range(0,9):
				if l in [1,3,5,7]: #checks for side pieces
					if board[l] == 0:
						i = l
	return i

#moves robot using robot commands to whichever spot was selected
def move_bot(index):
	global pickup_place_counter
	pickup_place_counter +=1
	pickup_places = ["out1", "out2", 'out3', 'out4']
	index_to_square_num = {0:"square1", 1:"square2", 2:"square3", 3: "square4", 4:"square5", 5:"square6", 6:"square7", 7:"square8", 8:"square9"}
	
	activate_gripper()
	move_robot_j(degrees_to_radians("top")) #go up each time to avoid bumping into anything
	time.sleep(5)
	open_gripper()
	time.sleep(3)
	pickup_place = str(pickup_places[pickup_place_counter])
	move_robot_j(degrees_to_radians(pickup_place)) #move to pickup spot that hasnt been used
	time.sleep(5)
	close_gripper()
	time.sleep(3)
	move_robot_j(degrees_to_radians("top"))
	time.sleep(5)
	pose = degrees_to_radians(index_to_square_num[index]) #move to selected square
	move_robot_j(pose)
	time.sleep(5)
	open_gripper()
	time.sleep(5)
	move_robot_j(degrees_to_radians("top"))
	time.sleep(5)

#picks a spot for robot; first checks if can win on next move, then block player, then corner spots, then center, then remaining places in between corners
def cpu_piece(board):
	i = 9
	num = block_player(board)
	num2 = cpu_winning_move(board)
	if num2 != 10: #cpu can win game on next move
		i = num2
	elif num != 10: #cpu can block player on next move
			i = num
	else:
		i = select_square(board)
	board[i] = 2
	return [i, board]

#variety of utterances to choose from right before robot puts its piece down
def utter():
	utterances = ["Let me see where I should put my piece.", "Don't be impatient. I'm thinking about where to place my piece...", "Ah I see what you did there. Let me think where to put my piece", "I will now place my piece"]
	
	global utterance_counter
	utterance_counter +=1
	if utterance_counter == 4:
		utterance_counter = 0
	return utterances[utterance_counter]


#places piece based on where places its piece and responds to player moves
def play_game(blue_list, image, dup_board, board): #player always goes first
	detect_player_piece(blue_list, image, dup_board, board)
	global break_var
	if has_won_all(board) == 3 and break_var == False:
		talk(utter()) #do this when person's piece is detected
		i = cpu_piece(board)[0]
		move_bot(i)
		if has_won_all(board) == 3:
			talk("your turn")
	
class Stream(object):
	
	def __init__(self):
		self.sub = rospy.Subscriber("/kinect2/hd/image_color", Image, self.sub_callback)
		self.bridge = CvBridge()
		self.image = None
		self.black = None
		self.image_hsv = None   
		self.pixel = (20,60,80) # arbitrary default
		self.on_board = [0,0,0,0,0,0,0,0,0] #entire board, all pieces
		self.blue_count_list = [0,0,0,0,0,0,0,0,0] #player pieces
		self.command_var = False
		self.duplicate_board = [0,0,0,0,0,0,0,0,0] #board to compare previous board to

	def sub_callback(self, data):
		self.image = self.bridge.imgmsg_to_cv2(data, "bgr8")
	
	#displays image and then plays game if neither player has won	
	def example_function(self):
		getImage = 0
		fourcc = cv2.cv.CV_FOURCC(*'XVID')
		video_writer = cv2.VideoWriter("/home/sar/catkin_ws/src/skill_assessment/kinect_perception/video.avi", fourcc, 20, (700, 500))
		while (not rospy.is_shutdown()) and getImage == 0 and has_won_all(self.on_board)==3:
			while self.image is None:
				rospy.logwarn("Image not being received...")
				rospy.sleep(1)
				
			cv2.namedWindow('bgr', cv2.WINDOW_NORMAL)
			cv2.resizeWindow("bgr", 800, 500)
			cropped = self.image[100:800, 1000:1500]
#			find_range_for_all_squares(cropped)
			#Show RGB images
			cv2.imshow("bgr", cropped)
			key = cv2.waitKey(1) & 0xFF
#			cv2.imshow("bgr", find_range_for_all_squares(cropped))
#			key = cv2.waitKey(1) & 0xFF
			global start_of_game
			if start_of_game:
				talk("Let's play Tic Tac Toe! I'll wait for you to put your piece down!")
			#checking whether person has put piece down

#			if global frame_count == 3:
#				talk("Hurry up with your piece!")
			start_of_game = False
#			detect_player_piece(self.blue_count_list, cropped, self.on_board)
			play_game(self.blue_count_list, cropped, self.duplicate_board, self.on_board)
			getImage = 0
#			time.sleep(15) #wait for player to put piece
			

		if has_won_all(self.on_board)==2:
			talk("Looks like I won! Better luck next time!")
			f.write("i won")
		elif has_won_all(self.on_board)==1:
			talk("Wow you beat me! Nice job! Rematch?")
			f.write("you won")
		

		cv2.destroyAllWindows()
		s.close()



if __name__ == "__main__":
	rospy.init_node("get_image")
	r = Stream()
	r.example_function()
#detect winning comments

	  
