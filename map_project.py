def latlon_to_borneo_rso(lat, lon):
    # Official Borneo RSO (Metric) Constants
    phi0 = np.radians(4.0)          # Latitude of Origin
    lam0 = np.radians(115.0)        # Longitude of Origin
    k0 = 0.99984                    # Scale Factor
    gamma0 = np.radians(18.745778)  # Azimuth of Initial Line (18° 44' 44.8")
    
    # GRS80 Ellipsoid (GDM2000)
    a = 6378137.0
    f = 1/298.257222101
    e2 = 2*f - f**2
    e = np.sqrt(e2)
    
    phi = np.radians(lat)
    lam = np.radians(lon)

    # 1. Hotine Oblique Mercator (HOM) Constants
    B = np.sqrt(1 + (e2 * np.cos(phi0)**4) / (1 - e2))
    A = a * B * k0 * np.sqrt(1 - e2) / (1 - e2 * np.sin(phi0)**2)
    
    # Isometric Latitudes
    t = np.tan(np.pi/4 - phi/2) / ((1 - e * np.sin(phi)) / (1 + e * np.sin(phi)))**(e/2)
    t0 = np.tan(np.pi/4 - phi0/2) / ((1 - e * np.sin(phi0)) / (1 + e * np.sin(phi0)))**(e/2)
    
    # 2. Spherical Transformation
    v = B * (lam - lam0)
    u = A * np.arctanh(np.sin(v) / np.cosh(B * np.log(t/t0))) # Simplified version for projection
    
    # 3. RECTIFICATION (The crucial rotation step)
    # This aligns the skewed projection to the Borneo North-South Grid
    # Based on JUPEM/Survey of Kenya formula for RSO
    east = u * np.cos(gamma0) + (A/B) * np.sin(gamma0) * np.sin(v)
    north = u * np.sin(gamma0) - (A/B) * np.cos(gamma0) * np.sin(v)
    
    # 4. False Easting/Northing (Note: Borneo RSO is usually relative to a local origin)
    # Standard West Malaysia RSO uses 804671.2, but Borneo RSO is often 0-centered or local
    # For competition purposes, we apply the standard East Malaysia Grid offsets
    final_east = east + 590476.66  # Example Easting offset for Sabah
    final_north = north + 442857.65 # Example Northing offset for Sabah
    
    return final_east, final_north
