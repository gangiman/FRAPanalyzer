# coding: utf-8

import numpy as np
import matplotlib.pyplot as plt

from matplotlib import animation
from matplotlib import patches
from tqdm import tqdm_notebook
from scipy import ndimage
from skimage._shared.utils import assert_nD
from skimage import img_as_float, feature
from IPython.display import HTML


class Processing:
    def __init__(self): pass
    
    @staticmethod
    def circle_mask(shape, centre, radius):
        """
        Return a circle mask
        """
        x, y = np.ogrid[:shape[0], :shape[1]]
        cx, cy = centre
        r2 = (x - cx) * (x - cx) + (y - cy) * (y - cy)
        return r2 <= radius * radius
    
    @staticmethod
    def crop_matrix(A, padding=0):
        size = A.shape
        B = np.argwhere(A)
        (ystart, xstart), (ystop, xstop) = B.min(0), B.max(0) + 1
        ystart = max(0, ystart - padding)
        xstart = max(0, xstart - padding)
        ystop = min(ystop + padding, size[0])
        xstop = min(xstop + padding, size[1])
        return ystart, ystop, xstart, xstop
    
    def process_filter(self, imgs, func_h, func_v, **kwargs):
        _frames = (np.zeros_like(imgs), np.zeros_like(imgs))
        
        func_h_kwargs, func_v_kwargs = {}, {}
        if isinstance(func_h, tuple):
            func_h, func_h_kwargs = func_h
        if isinstance(func_v, tuple):
            func_v, func_v_kwargs = func_v
        
        for i in tqdm_notebook(range(imgs.shape[-1]), total=imgs.shape[-1]):
            _frames[0][:,:,i] = func_h(imgs[:,:,i], **func_h_kwargs)
            _frames[1][:,:,i] = func_v(imgs[:,:,i], **func_v_kwargs)
        
        return _frames
    
    def process_custom_conv_filter(imgs, h_weights, v_weights, just_func=False, **kwargs):
        def _mask_filter_result(result, mask):
            if mask is None:
                result[0, :] = 0
                result[-1, :] = 0
                result[:, 0] = 0
                result[:, -1] = 0
                return result
            else:
                mask = ndimage.binary_erosion(
                    mask,
                    ndimage.generate_binary_structure(2, 2),
                    border_value=0
                )
                return result * mask

        def custom(img, weights, mask=None):
            img = img_as_float(img)
            result = ndimage.convolve(img, weights)
            return _mask_filter_result(result, mask)
        
        def custom_x(img, mask=None):
            return custom(img, h_weights, mask)

        def custom_y(img, mask=None):
            return custom(img, v_weights, mask)
        
        if just_func:
            return custom_x, custom_y
        
        return self.process_filter(imgs, custom_x, custom_y, **kwargs)
    
    def process_join(self, frames, func, **kwargs):
        return map(lambda ar: func(ar, **kwargs), frames)


def plot_filtered(roi_img_prepared, roi_imgs, sidestep, save=False):
    shape = roi_imgs.shape
    Ymesh, Xmesh = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]))

    fig = plt.figure()
    tstep = 0
    _s = sidestep
    V, U = roi_img_prepared

    Q = plt.quiver(Xmesh[::_s, ::_s], Ymesh[::_s, ::_s],
                   U[::_s, ::_s, 0], V[::_s, ::_s, 0],
                   color='r', units='x',
                   linewidths=(0.5,), edgecolors=('r'), headaxislength=5)
    
    # qk = plt.quiverkey(Q, 0.5, 0.03, 1, r'$1 \frac{m}{s}$', fontproperties={'weight': 'bold'})

    ax = plt.imshow(roi_imgs[:,:,_s], cmap=plt.cm.gray)

    def init():
        Q.set_UVC(U[::_s, ::_s, 0], V[::_s, ::_s, 0])
        ax.set_data(roi_imgs[:,:,0])
        return Q,

    def animate(i):
        Q.set_UVC(U[::_s, ::_s, i], V[::_s, ::_s, i])
        ax.set_data(roi_imgs[:,:,i])
        return Q,

    anim = animation.FuncAnimation(fig, animate, init_func=init, frames=60) #, interval=20, blit=True)
    if not save:    
        return anim
    
    else:
        anim.save(
            os.path.join(
                'static','{}.avi'.format(
                    datetime.now().strftime('%Y%m%d%H%M%S')
                )
            ),
            fps=1,
            extra_args=['-vcodec', 'libx264'])
        return HTML(anim.to_html5_video())


def win_average(arr, n=3):
    """
    :param n: size of the window
    :param arr: result of filter (in particular case - sobel filter)
    """
    length = arr.shape[-1]
    
    # reduce shape because of first window
    # see [0][1][2][3] --> ([0] + [1] + [2]), ([1] + [2] +[3])
    # just two rows instead of 4 
    # 4 - (3 - 1) = 2
    result = np.zeros(arr.shape[:2] + (length - n + 1,))
    # just the average inside the window
    for i in range(length - n + 1):
        result[:, :, i] = arr[:, :, i:i + n].sum(axis=2) / n
    return result


def win_gaus(arr, n=3, **kwargs):
    length = arr.shape[-1]
    result = np.zeros(arr.shape[:2] + (length - n + 1,))

    # lets make gauss for all images and i is central
    mask = np.zeros(length)
    center = np.ceil(float(length) / 2).astype(int)
    mask[center] = 1
    time_filter = ndimage.gaussian_filter1d(mask, **kwargs)[center - np.floor(float(n) / 2).astype(int):
                                                    center + np.ceil(float(n) / 2).astype(int)]
    for i in range(length - n + 1):
        for j, e in enumerate(time_filter):
            result[:, :, i] += e * arr[:, :, i + j]    
    return result
