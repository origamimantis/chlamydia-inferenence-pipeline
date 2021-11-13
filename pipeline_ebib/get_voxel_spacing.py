import subprocess

def getspacing(path):
    result = subprocess.run(['header', '-p', path], stdout=subprocess.PIPE)
    ret = result.stdout.split()
    for i in range(len(ret)):
        ret[i] = eval(ret[i])
    return ret

