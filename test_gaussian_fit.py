import numpy as np
from lmfit.models import Model, LinearModel
from lmfit.models import GaussianModel, LorentzianModel
import matplotlib.pyplot as plt

def generate_gaussian(amp, mu, sigma_sq, slope=0, const=0):
    x = np.linspace(mu-10*sigma_sq, mu+10*sigma_sq, num=200)
    y_gauss = (amp/np.sqrt(2*np.pi*sigma_sq))*np.exp(-0.5*(x-mu)**2/sigma_sq)
    y_linear = slope*x + const
    y = y_gauss + y_linear
    return x, y

# Gaussiand peak generation
amplitude = 6
center = 3884
variance = 4
slope = 0
intercept = 0.05
x, y = generate_gaussian(amplitude, center, variance, slope, intercept)


#Create a lmfit model: Gaussian peak + linear background
gaussian = GaussianModel()
background = LinearModel()
model = gaussian + background

#Find what model parameters you need to specify
print('parameter names: {}'.format(model.param_names))
print('independent variables: {}'.format(model.independent_vars))

#Model fit
result = model.fit(y, x=x, amplitude=3, center=3880,
                   sigma=3, slope=0, intercept=0.1)
y_fit = result.best_fit #the simulated intensity
