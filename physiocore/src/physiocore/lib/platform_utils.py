# Have platform specific things go here
import platform

import cv2

save_video_codec_mac = cv2.VideoWriter_fourcc('M','J','P','G')
save_video_codec_win = cv2.VideoWriter_fourcc(*'MP4V')
save_video_codec_linux = cv2.VideoWriter_fourcc(*'XVID')

save_video_codec = None

if platform.system() == 'Darwin':
	save_video_codec = save_video_codec_mac
elif platform.system() == 'Windows':
	save_video_codec = save_video_codec_win
else:
	save_video_codec = save_video_codec_linux
