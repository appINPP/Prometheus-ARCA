def KM3_sphere() -> np.ndarray:
    #Custom PMT positions for KM3NeT
    t=np.array([90,58,58,58,58,58,58,34,34,34,34,34,34,17,17,17,17,17,17,-17,-17,-17,-17,-17,-17,-34,-34,-34,-34,-34,-34])
    thetad=t+90
    phid=np.array([0,30,330,270,210,150,90,0,300,240,180,120,60,30,330,270,210,150,90,0,300,240,180,120,60,30,330,270,210,150,90])
    theta=np.radians(thetad)
    phi=np.radians(phid)
    return np.column_stack(
        [
            np.sin(theta) * np.cos(phi),
            np.sin(theta) * np.sin(phi),
            np.cos(theta),
        ]
    )


# Pre-computed PMT directions in the module frame (fixed, z-axis = string axis).
PMT_DIRS: np.ndarray = KM3_sphere()  # shape (31,3) in km3net

