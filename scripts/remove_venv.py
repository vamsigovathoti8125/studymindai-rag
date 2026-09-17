import shutil, os
shutil.rmtree('venv', ignore_errors=True)
print('venv removed' if not os.path.exists('venv') else 'venv still exists')
