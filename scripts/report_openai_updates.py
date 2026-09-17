files=['app.py','src/vectorstore.py','src/agent/agent.py','src/tools/quiz_tool.py','src/tools/summary_tool.py']
patterns=['from openai import OpenAI','client = OpenAI','client.chat.completions.create','client.embeddings.create','os.getenv("OPENAI_API_KEY")']

for f in files:
    try:
        with open(f,'r',encoding='utf-8') as fh:
            lines=fh.readlines()
    except FileNotFoundError:
        print(f'{f}: NOT FOUND')
        continue
    print(f'\n{f}:')
    for i,l in enumerate(lines, start=1):
        for p in patterns:
            if p in l:
                print(f'  L{i}: contains "{p}"')
