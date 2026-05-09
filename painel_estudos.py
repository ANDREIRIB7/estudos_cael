import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

# Configurações de Pesos e Incidência (Base BB 2023 / Cesgranrio)
# Incidência: Quão frequente o tema é cobrado dentro daquela matéria (ajustável)
CONFIG_MATERIAS = {
    'Português': {'peso': 1.5, 'questoes': 10, 'incidencia': 0.85},
    'Matemática': {'peso': 1.5, 'questoes': 5, 'incidencia': 0.70},
    'Inglês': {'peso': 1.0, 'questoes': 5, 'incidencia': 0.50},
    'Atualidades MF': {'peso': 1.0, 'questoes': 5, 'incidencia': 0.90},
    'Informática': {'peso': 1.5, 'questoes': 15, 'incidencia': 0.95},
    'Vendas e Negociação': {'peso': 1.5, 'questoes': 15, 'incidencia': 0.90},
    'Conhecimentos Bancários': {'peso': 1.5, 'questoes': 10, 'incidencia': 0.95},
    'Matemática Financeira': {'peso': 1.5, 'questoes': 5, 'incidencia': 0.80}
}

def inicializar_sistema():
    conn = sqlite3.connect('controle_estudos.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resultados_simulados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            materia TEXT,
            acertos INTEGER,
            total_questoes INTEGER
        )
    ''')
    conn.commit()
    return conn

def registrar_simulado_completo(dados_acertos):
    """
    dados_acertos: dict no formato {'Materia': acertos}
    """
    conn = inicializar_sistema()
    cursor = conn.cursor()
    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    for materia, acertos in dados_acertos.items():
        total = CONFIG_MATERIAS[materia]['questoes']
        cursor.execute('''
            INSERT INTO resultados_simulados (data, materia, acertos, total_questoes)
            VALUES (?, ?, ?, ?)
        ''', (data_atual, materia, acertos, total))
    
    conn.commit()
    conn.close()
    print(f"✅ Simulado de {data_atual} registrado!")

def gerar_painel_controle():
    conn = inicializar_sistema()
    df = pd.read_sql_query("SELECT * FROM resultados_simulados", conn)
    conn.close()
    
    if df.empty:
        return "Sem dados para gerar o painel."

    # 1. Cálculo de Performance Ponderada por matéria
    resultados = []
    for materia, config in CONFIG_MATERIAS.items():
        materia_df = df[df['materia'] == materia]
        if not materia_df.empty:
            acerto_medio = materia_df['acertos'].sum() / materia_df['total_questoes'].sum()
            # Fórmula proposta: Acerto * Peso * Incidencia
            performance = acerto_medio * config['peso'] * config['incidencia']
            max_possivel = 1.0 * config['peso'] * config['incidencia']
            
            resultados.append({
                'Matéria': materia,
                'Acerto Real %': round(acerto_medio * 100, 1),
                'Subtotal (IPP)': round(performance, 3),
                'Peso na Evolução': round((performance / max_possivel) * 100, 1)
            })
    
    painel_df = pd.DataFrame(resultados)
    
    # 2. Cálculo da Média Móvel de Evolução Total
    # Agrupamos por data para ver a nota ponderada total de cada simulado feito
    df['pontos_ponderados'] = df.apply(lambda row: (row['acertos']/row['total_questoes']) * CONFIG_MATERIAS[row['materia']]['peso'] * CONFIG_MATERIAS[row['materia']]['incidencia'], axis=1)
    
    evolucao_por_data = df.groupby('data')['pontos_ponderados'].sum().reset_index()
    evolucao_por_data['Media_Movel_5'] = evolucao_por_data['pontos_ponderados'].rolling(window=5, min_periods=1).mean()
    
    print("\n" + "="*50)
    print("🚀 PAINEL DE EVOLUÇÃO ESTRATÉGICA (IPP)")
    print("="*50)
    print(painel_df.sort_values(by='Subtotal (IPP)', ascending=False).to_string(index=False))
    print("-"*50)
    
    ultima_media = evolucao_por_data['Media_Movel_5'].iloc[-1]
    tendencia = "📈 CRESCENTE" if len(evolucao_por_data) > 1 and ultima_media > evolucao_por_data['Media_Movel_5'].iloc[-2] else "📉 ESTAGNADO/QUEDA"
    
    print(f"STATUS ATUAL DA MÉDIA MÓVEL: {round(ultima_media, 2)}")
    print(f"TENDÊNCIA DE PERFORMANCE: {tendencia}")
    print("="*50)

# --- EXECUÇÃO ---
if __name__ == "__main__":
    # Simulando a entrada de dados do seu primeiro simulado diagnóstico
    meu_primeiro_simulado = {
        'Português': 7, 'Matemática': 3, 'Inglês': 4, 'Atualidades MF': 5,
        'Informática': 10, 'Vendas e Negociação': 14, 'Conhecimentos Bancários': 6,
        'Matemática Financeira': 2
    }
    
    # registrar_simulado_completo(meu_primeiro_simulado)
    gerar_painel_controle()