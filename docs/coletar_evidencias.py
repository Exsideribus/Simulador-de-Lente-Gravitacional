"""Coleta números e benchmarks do simulador; não altera seus módulos."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import ast, hashlib, importlib.metadata, inspect, json, platform, sys, time
from pathlib import Path
from datetime import date
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
from PyQt6.QtWidgets import QApplication
from core.cosmologia import cosmo
from core.equacoes import SimuladorLente
from core.geometria import calcular_geometria
from render.ray_tracing import MotorRenderizacao
from ui.janela import JanelaSimulador

def versao(p):
    try:
        return importlib.metadata.version(p)
    except importlib.metadata.PackageNotFoundError:
        return "não instalado (ou sem metadados)"

arcsec = np.pi / (180 * 3600)
app = QApplication.instance() or QApplication([])
s = SimuladorLente(2e42, .5, 2)
nominal = float(s.theta_E / arcsec)
m = MotorRenderizacao(800,800,10)
j = JanelaSimulador(m,s,0,0,.2*arcsec)
g = j.diagrama.geometria
packages = ["numpy","astropy","pyqtgraph","PyQt6","scipy","numba"]
data = {
    "data":date.today().isoformat(), "python":sys.version, "kernel":platform.release(),
    "versoes":{p:versao(p) for p in packages},
    "qt":QT_VERSION_STR,"pyqt":PYQT_VERSION_STR,"backend_teste":app.platformName(),
    "cosmologia":str(cosmo), "assinatura_distancia":str(inspect.signature(cosmo.angular_diameter_distance)),
    "numeros":{
        "Dl_Mpc":s.Dl/3.08567758e22, "Ds_Mpc":s.Ds/3.08567758e22,
        "Dls_Mpc":s.Dls/3.08567758e22,
        "chi_l_Mpc":s.Dl*(1+s.z_l)/3.08567758e22,
        "chi_s_Mpc":s.Ds*(1+s.z_s)/3.08567758e22,
        "thetaE_nominal_arcsec":nominal, "thetaE_UI_arcsec":s.theta_E/arcsec,
        "massa_UI_kg":s.M, "massa_UI_solar":s.M/1.989e30,
        "sigma_UI_arcsec":j.sigma/arcsec,"fracao_lente":g.fracao_lente,
        "passo_pixel_arcsec":10/799, "fonte_posicao_max_arcsec":250*1e-7/arcsec,
        "fonte_posicao_passo_arcsec":1e-7/arcsec,
        "sigma_min_arcsec":1e-8/arcsec,"sigma_max_arcsec":200e-8/arcsec,
        "raios_alinhados":len(g.raios),
        "beta_obs_1kpc_arcsec":float(calcular_geometria(s,0,0,j.sigma,1,0).beta_efetivo[0]/arcsec),
        "central_singular_beta":list(map(float,s.equacao_lente_inversa(np.array(0.),np.array(0.)))),
        "buffer_persistente_MiB":sum(getattr(m,k).nbytes for k in ["theta_x","theta_y","textura","fundo","raio"])/2**20,
    }, "benchmarks":[], "fontes":{}
}
for n in (400,800,1200):
    motor=MotorRenderizacao(n,n,10)
    def rodada():
        geo=calcular_geometria(s,0,0,j.sigma)
        frame=motor.renderizar_frame(s,*geo.beta_efetivo,j.sigma)
        motor.renderizar_telescopio(s,frame)
    for _ in range(3): rodada()
    amostras=[]
    for _ in range(20):
        t=time.perf_counter(); rodada(); amostras.append((time.perf_counter()-t)*1000)
    data["benchmarks"].append({"resolucao":n,"amostras":20,
        "mediana_ms":float(np.median(amostras)), "p95_ms":float(np.percentile(amostras,95)),
        "min_ms":min(amostras),"max_ms":max(amostras)})
for _ in range(3): j.atualizar_render()
tempos=[]
for _ in range(20):
    t=time.perf_counter(); j.atualizar_render(); tempos.append((time.perf_counter()-t)*1000)
data["UI_atualizar_sem_pintura"]={"mediana_ms":float(np.median(tempos)),"p95_ms":float(np.percentile(tempos,95))}
for name in ["main.py","core/cosmologia.py","core/equacoes.py","core/geometria.py",
             "render/gerador_fonte.py","render/ray_tracing.py","ui/janela.py","ui/diagrama.py",
             "tests/test_visualizacoes.py","tests/test_plataforma.py","requeriments.txt"]:
    p=ROOT/name
    item={"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
    if p.suffix==".py":
        source=p.read_text(encoding="utf-8-sig")
        item["linhas"]=len(source.splitlines())
        item["simbolos"]={node.name:node.lineno for node in ast.walk(ast.parse(source))
                         if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    data["fontes"][name]=item
j.close()
saida=ROOT/"docs"/"evidencias_tecnicas.json"
saida.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in data.items() if k!="fontes"},ensure_ascii=False,indent=2))