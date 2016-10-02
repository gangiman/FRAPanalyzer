import numpy as np
import openpiv

def get_piv_flow(frame_a, frame_b):
    u, v, sig2noise = openpiv.process.extended_search_area_piv(
        frame_a.astype(np.int32), frame_b.astype(np.int32),
        window_size=24, overlap=12, dt=0.02, search_area_size=64,
        sig2noise_method='peak2peak')

    x, y = openpiv.process.get_coordinates(image_size=frame_a.shape, window_size=24, overlap=12)
    u, v, mask = openpiv.validation.sig2noise_val(u, v, sig2noise, threshold=1.3)
    u, v, mask = openpiv.validation.global_val(u, v, (-1000, 2000), (-1000, 1000))
    u, v = openpiv.filters.replace_outliers(u, v, method='localmean', max_iter=10, kernel_size=2)
    x, y, u, v = openpiv.scaling.uniform(x, y, u, v, scaling_factor=96.52)
    return x, y, u, v, mask

    # openpiv.tools.save(x, y, u, v, mask, 'exp1_001.txt')
    # openpiv.tools.display_vector_field('exp1_001.txt', scale=100, width=0.0025)

def plot_piv_flow(a, b, axes=None):
    x, y, u, v, mask = get_piv_flow(a, b)
    # a = np.loadtxt(filename)
    # fig=axes.figure()
    axes.hold(True)
    # if on_img: # plot a background image
    #     im = imread(image_name)
    #     im = negative(im) #plot negative of the image for more clarity
    #     imsave('neg.tif', im)
    #     im = maxestimg.imread('neg.tif')
    #     xmax=np.amax(a[:,0])+window_size/(2*scaling_factor)
    #     ymax=np.amax(a[:,1])+window_size/(2*scaling_factor)
    #     implot = axes.imshow(im, origin='lower', cmap="Greys_r",extent=[0.,xmax,0.,ymax])
    # invalid = a[:,4].astype('bool')
    # fig.canvas.set_window_title('Vector field, '+str(np.count_nonzero(invalid))+' wrong vectors')
    valid = ~mask
    axes.quiver(x[mask], y[mask], u[mask], v[mask], color='r')
    axes.quiver(x[valid], y[valid], u[valid], v[valid], color='b')
    axes.hold(False)
    # axes.draw()
    # axes.show()
