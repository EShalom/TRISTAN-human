import numpy as np
import os
import time
import itk
import mdreg
from utilities import helper

def setup_mdreg(info, fit_interval = None):
    '''Main function for DCE model-driven registration
        
    Returns:
        None
    
    '''
    subject, visit, scan = info['subject'], info['visit'], info['scan']
    subject_path = os.path.join(f'Subject_{subject}', f'Visit_{visit}', f'Scan_{scan}')
    coreg_path = os.path.join(info['output_path'],'coreg', subject_path)
    aif_path = os.path.join(info['output_path'],'aif', subject_path)
    
    logger = info['logger']

    helper.check_dirs_exist(coreg_path)

    if end_point is None:
        logger.info("End point not specified, fitting full dynamic data")

    logger.info(f"Running coregistration for Subject {subject}, Visit {visit}, Scan {scan}")
    logger.info(f"Starting aif and dynamic data loading")
    
    aif = np.load(f"{aif_path}\\s{subject}_v{visit}_s{scan}_aif.npz",allow_pickle=True)['aif'] 
    
    logger.info(f"Loaded aif for Subject {subject}, Visit {visit}, Scan {scan}")
    
    data = np.load(f"{info['data_path']}\\combined_dynamic.npz",allow_pickle=True)
    
    logger.info(f"Loaded dynamic data for Subject {subject}, Visit {visit}, Scan {scan}")
    
    # Set interval if ony want to motionn correction only part of the full dynamic
    # Default is 0 which returns the entire array found in combined_dynamic.npz
    
    if fit_interval:
        start_point, end_point = fit_interval
    elif not fit_interval:
        start_point = 0
        end_point = None
    
    array = data['data'][:,:,:,start_point:end_point]
    aif = aif[start_point:end_point]
    time_array = data['timepoints'][start_point:end_point]
    time_array = (time_array - time_array[0])/1000
    spacing = data['spacing']

    logger.info("Adjusted time array")
    if scan == 1:
        baseline = int(np.floor(60/time_array[1]))
    if scan == 2:
        baseline = int(np.floor(300/time_array[1]))
    
    logger.info(f"Calculated baseline: timepoint {baseline}")

    tristan_fit = {
    'func': mdreg.array_2cfm_lin,  # The function to fit the data
    'aif': aif,  # The arterial input function
    'time': time_array,  # The time points
    'baseline': baseline,  # The header information
    'Hct': 0.45
}

    coreg_params = {
        'package': 'elastix',
        'FinalGridSpacingInPhysicalUnits': 50.0,
        'spacing': spacing
    }

    coreg, defo, fit, pars = mdreg.fit(array,
                                    fit_image=tristan_fit, 
                                    fit_coreg=coreg_params,
                                    maxit=5, 
                                    verbose=2)
                                    
                                    

    np.savez_compressed('{}\\Sub{}_V{}_S{}_coreg.npz'.format(coreg_path, subject, visit, scan), coreg=coreg, fit=fit, pars=pars, spacing=spacing)

    return  