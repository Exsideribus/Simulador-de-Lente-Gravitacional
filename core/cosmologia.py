from astropy.cosmology import FlatLambdaCDM

# Cosmologia (Plank 2018)
cosmo = FlatLambdaCDM(H0=67.4, Om0=0.315)

def calcular_distancia(z_l, z_s):
    '''
    Calcula a distância de diâmetro angular
    z_l -> Redshift da lente
    z_s -> Redshift da fonte
    return -> Dl, Ds, Dls em metros
    '''

    if z_l >= z_s:
        raise ValueError("O redshift da lente deve ser menor que a fonte")
    
    Mpc_to_m = 3.08567758e22

    Dl = cosmo.angular_diameter_distance(z_l).value * Mpc_to_m
    Ds = cosmo.angular_diameter_distance(z_s).value * Mpc_to_m
    Dls = cosmo.angular_diameter_distance(z_l, z_s).value * Mpc_to_m

    return Dl, Ds, Dls