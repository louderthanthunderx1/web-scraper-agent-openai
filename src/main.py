from agent.agent import run_agent

while True:
    query = input("> ")
    res = run_agent(query)
    print(res)
