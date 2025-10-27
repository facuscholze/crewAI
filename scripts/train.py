from integrado.crew import Integrado

n_iterations = 5
inputs = {"topic": "Tu tema aquí"}
filename = "trained_agents_data.pkl"

try:
    Integrado().crew().train(
        n_iterations=n_iterations,
        inputs=inputs,
        filename=filename
    )
except Exception as e:
    print(f"Error al entrenar: {e}")