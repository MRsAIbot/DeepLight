"""
@author: Tobias Rijken

Code to plot the 2D t-SNE embedding

usage: python tsne_plot.py tsne_file labels_file

"""

import sys
import cPickle
import matplotlib.pyplot as plt
from matplotlib import cm

def main(tsne_file, labels_file):
	with open(tsne_file, 'r') as f:
		Y = cPickle.load(f)
	with open(labels_file, 'r') as f:
		labels = cPickle.load(f)
	# print Y
	# print Y.shape
	# print len(Y)
	# print Y[2]
	# for i in range(len(Y)):
	# 	if 85.0 < Y[i][0] < 86.0 and 85.0 < Y[i][1] < 86.0:
	# 		print i
	# 	if 25.0 < Y[i][0] < 26.0 and 105.0 < Y[i][1] < 106.0:
	# 		print i
	# 	if -79.0 < Y[i][0] < -77.0 and -9.0 < Y[i][1] < -8.0:
	# 		print i
	# 	if 52.0 < Y[i][0] < 53.0 and -87.0 < Y[i][1] < -86.5:
	# 		print i
	print Y[4119]
	print Y[9065]
	print Y[6588]
	print Y[8675]
	plt.scatter(Y[:,0], Y[:,1], 20, labels, cmap=cm.jet)
	plt.colorbar()
	plt.annotate('I', xy=(Y[9065][0], Y[9065][1]), xytext=(125,125), \
		arrowprops=dict(facecolor='black', shrink=0.05))
	plt.annotate('II', xy=(Y[4119][0], Y[4119][1]), xytext=(50,125), \
		arrowprops=dict(facecolor='black', shrink=0.05))
	plt.annotate('III', xy=(Y[6588][0], Y[6588][1]), xytext=(-125,-100), \
		arrowprops=dict(facecolor='black', shrink=0.05))
	plt.annotate('IV', xy=(Y[8675][0], Y[8675][1]), xytext=(100,-125), \
		arrowprops=dict(facecolor='black', shrink=0.05))
	plt.xlabel('x')
	plt.ylabel('y')
	plt.show()

if __name__ == '__main__':
	tsne_file = sys.argv[1]
	labels_file = sys.argv[2]
	main(tsne_file, labels_file)