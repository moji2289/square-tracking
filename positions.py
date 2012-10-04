import matplotlib.pyplot as pl
import matplotlib.cm as cm
import numpy as np
from scipy.stats import nanmean
from PIL import Image as Im
import sys


#extdir = '/Volumes/Walsh_Lab/2D-Active/spatial_diffusion/'
locdir = '/Users/leewalsh/Physics/Squares/spatial_diffusion/'
prefix = 'n08'

plottracks = True
domsd   = False

bgimage = Im.open(locdir+'/n8_0001.tif') # for bkground in plot
datapath = locdir+prefix+'_4500.txt'

### Add 'ID' as label for first column in first line !!! ###

data = [ line[:-1] for line in open(datapath)] # last char in each line is newline
datatypes = data[0].split()#('/t') # split with no arg figures it out
data = [ dataline.split() for dataline in data[1:] ] # remove first line, split each column
for dot in data:
    dot.append(0.0)
    dot.append(0.0)
data = np.array(data).astype(float)

# indices in file (number gives column)
iid =    datatypes.index('ID')    # unique particle id
iarea =  datatypes.index('Area')  # particle 
ix =     datatypes.index('X')     # x position
iy =     datatypes.index('Y')     # y position
islice = datatypes.index('Slice') # slice (image frame) number
isid = len(datatypes)             # static id (tracks particles)
idisp = isid + 1                  # particle displacement from initial position
if (max(idisp,isid) + 1) > len(data[0]):
    print "too many column indices"

# recursive function to find nearest dot in previous frame.
# looks further back until it finds the nearest particle
sys.setrecursionlimit(2000)
giveup=1999
def find_closest(thisdot,slice,n=1,maxdist=20.,giveup=500):
    if slice < n:  # back to the first frame
        newsid = max(data[:,isid]) + 1
        print "New track:",newsid
        print '\tslice:', slice,'n:', n,'dot:', thisdot[iid]
    else:
        oldframe = data[np.nonzero(data[:,islice]==slice-n+1)]
        dist = maxdist
        for olddot in oldframe:
            newdist = (newdot[ix]-olddot[ix])**2 + (newdot[iy]-olddot[iy])**2
            if newdist < dist:
                dist = newdist
                newsid = olddot[isid]
                #print "found it! (",newsid,"slice:",slice,'; n:',n,')'
        if (n < giveup) & (dist >= maxdist):
            #print "still looking...",dist,'>',maxdist
            newsid = find_closest(thisdot,slice,n=n+1,maxdist=maxdist,giveup=giveup)
        if n >= giveup: # give up after giveup frames
            print "recursed", n, "times, giving up. slice =", slice
            newsid = max(data[:,isid]) + 1
            print "created new static id:",newsid
    data[thisdot[iid]-1,isid] = newsid
    return newsid


nslice = int(data[len(data)-1][islice])
if domsd:
    msqdisp = np.zeros(nslice)
    dists = []
for slice in range(nslice):
    curr = np.nonzero(data[:,islice]==slice+1)

    # for first image, use original particle ID as statid ID
    if 0:#(slice == 0):
        firs = curr
        data[firs,isid] = data[firs,iid]
        #data[curr,idisp] = 0.0
        initx = data[firs,ix]
        inity = data[firs,iy]
    else:
        for newdot in data[curr]:
            newsid = find_closest(newdot,slice,giveup=giveup)
            #sqdisp = (newdot[ix] - olddot[ix])**2 + (newdot[iy]-olddot[iy])**2
            if domsd:
                sqdisp = (newdot[ix] - data[np.nonzero(data[:,iid]==newsid),ix])**2 \
                        + (newdot[iy] - data[np.nonzero(data[:,iid]==newsid),iy])**2
                data[newdot[iid]-1,idisp] = float(sqdisp) if bool(newsid) & (np.shape(sqdisp)==(1,1)) else None
        if domsd:
            msqdisp[slice] = nanmean(data[np.nonzero(data[:,islice]==slice+1),idisp][0])


# Plotting:
#nparticles = int(prefix[1:]) if ('n' in prefix) else int(max(data[:,isid]))
ntracks = int(max(data[:,isid]))
for trackn in range(ntracks):
    # filter out all dots that belong to this track:
    trackparts = np.nonzero(data[:,isid]==trackn+1)[0] # just want the column indices (not row)
    c = cm.spectral(1-float(trackn)/ntracks) #spectral colormap, use prism for more colors

    # Locations plotted over image:
    if plottracks:
        pl.figure(1)
        bgheight = bgimage.size[1] # for flippin over y
        pl.plot(data[trackparts,ix],bgheight-data[trackparts,iy],'.',color=c,label="track "+str(trackn+1))

    # Mean Squared Displacement:
    if domsd:
        pl.figure(2)
        #pl.loglog(data[np.nonzero(data[:,isid]==trackn+1)][:,idisp],color=c,label="track "+str(trackn+1))
        pl.loglog(data[trackparts,idisp],color=c,label="track "+str(trackn+1))

if plottracks:
    pl.figure(1)
    pl.imshow(bgimage,cmap=cm.gray,origin='lower')
    pl.title(prefix)
    pl.legend()

if domsd:
    pl.figure(2)
    pl.loglog(msqdisp,'ko') # mean
    pl.loglog(np.arange(nslice)+1,np.arange(nslice)+1,'k--') # slope = 1 for ref.
    pl.legend()
    pl.xlabel('Time (Image frames)')
    pl.ylabel('Squared Displacement'+r'$pixels^2$')

pl.show()
