import argparse
import json
import sys
from pathlib import Path

LINE_END = " \\" + "\n"

def portBindingsToString(jsonObject):
    stringResult = ""
    for key, value in jsonObject.items():
        hostIp = value[0]["HostIp"]
        hostPort = value[0]["HostPort"]

        if hostIp is None or len(hostIp) == 0:
            stringResult += "-p " + hostPort + ":" + key
        else:
            stringResult += "-p " + hostIp + ":" + hostPort + ":" + key
        stringResult += " "
    return stringResult

def parseName(name):
    if name is None:
        return None
    elif name[0].__eq__("/"):    
        return name[1:]
    else:
        return name

def parseUlimits(list):
    stringResult = ""
    for obj in list:
        name = obj["Name"]
        hard = obj["Hard"]
        soft = obj["Soft"]

        stringResult += "--ulimit "
        stringResult += name + "="

        if soft is not None:
             stringResult += str(soft)
        if hard is not None:
             stringResult += ":" + str(hard)

        stringResult += " "
    return stringResult        

def main():
    prog = 'docker inspect <container> | python3 parse-docker-inspect.py'
    description = ('A simple command line tool that will try to parse the json generated from docker inspect and reverse engineer that to create the docker-run command')
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument('infile', nargs='?',
                        type=argparse.FileType(encoding="utf-8"),
                        help='a JSON file to be validated or pretty-printed',
                        default=sys.stdin)
    parser.add_argument('outfile', nargs='?',
                        type=Path,
                        help='write the output of infile to outfile',
                        default=None)
    options = parser.parse_args()

    with options.infile as infile:
        try:
            objs = (json.load(infile),)
            if options.outfile is None:
                out = sys.stdout
            else:
                out = options.outfile.open('w', encoding='utf-8')
            with out as outfile:
                inspectObj = objs[0][0]
                configSection = inspectObj["Config"]
                hostConfigSection = inspectObj["HostConfig"]
                networkSettingsSection = inspectObj["NetworkSettings"]
                image = configSection["Image"]
                portString = portBindingsToString(hostConfigSection["PortBindings"])
                name = parseName(inspectObj["Name"])
                network = list(networkSettingsSection["Networks"].keys())[0]
                user = configSection["User"]
            
                stringBuilder = "docker run"
                if name:
                    stringBuilder += " --name " + name + LINE_END
                if network:
                    stringBuilder += " --network=" + network + LINE_END
                if user:
                    stringBuilder += " --user " + user + LINE_END                     
                if hostConfigSection["Privileged"]:
                    stringBuilder += " --privileged" + LINE_END
                if hostConfigSection["AutoRemove"]:
                    stringBuilder += " --rm" + LINE_END
                if hostConfigSection["Runtime"]:
                    stringBuilder += " --runtime " + hostConfigSection["Runtime"] + LINE_END
                if hostConfigSection["PublishAllPorts"]:
                    stringBuilder += "  --publish-all" + LINE_END                    
                if hostConfigSection["RestartPolicy"]:
                    stringBuilder += " --restart " + hostConfigSection["RestartPolicy"]["Name"]
                    if hostConfigSection["RestartPolicy"]["Name"] == "on-failure":
                        stringBuilder += ":" + str(hostConfigSection["RestartPolicy"]["MaximumRetryCount"])
                    stringBuilder += LINE_END    
                if portString:
                    stringBuilder += " " + portString + LINE_END
                if hostConfigSection["Binds"]:
                    stringBuilder += ' -v ' + ' -v '.join(hostConfigSection["Binds"]) + LINE_END
                if hostConfigSection["VolumesFrom"]:
                    stringBuilder += ' --volumes-from ' + ' --volumes-from '.join(hostConfigSection["VolumesFrom"]) + LINE_END
                if hostConfigSection["Links"]:
                    stringBuilder += ' --link ' + ' --link '.join(hostConfigSection["Links"]) + LINE_END                    
                if hostConfigSection["Ulimits"]:
                    ulimitStrings = parseUlimits(hostConfigSection["Ulimits"])
                    stringBuilder += " " + ulimitStrings + LINE_END                
                if hostConfigSection["UTSMode"]:
                    stringBuilder += " --uts " + hostConfigSection["UTSMode"] + LINE_END
                if hostConfigSection["LogConfig"]:
                    stringBuilder += ' --log-driver ' + hostConfigSection["LogConfig"]["Type"] + LINE_END
                if hostConfigSection["ExtraHosts"]:
                    stringBuilder += ' --add-host=' + ' --add-host='.join(hostConfigSection["ExtraHosts"]) + LINE_END
                if hostConfigSection["Dns"]:
                    stringBuilder += ' --dns ' + ' --dns '.join(hostConfigSection["Dns"]) + LINE_END
                if hostConfigSection["CapAdd"]:
                    stringBuilder += ' --cap-add ' + ' --cap-add '.join(hostConfigSection["CapAdd"]) + LINE_END
                if hostConfigSection["CapDrop"]:
                    stringBuilder += ' --cap-drop ' + ' --cap-drop '.join(hostConfigSection["CapDrop"]) + LINE_END
                if configSection["Hostname"]:
                    stringBuilder += " --hostname " + configSection["Hostname"] + LINE_END
                if configSection["Domainname"]:
                    stringBuilder += " --domainname " + configSection["Domainname"] + LINE_END
                if (not configSection["AttachStdin"]) and (not configSection["AttachStdout"]) and (not configSection["AttachStderr"]):
                    stringBuilder += " --detach " + LINE_END
                if configSection["AttachStdin"]:
                    stringBuilder += " --attach stdin " + LINE_END
                if configSection["AttachStdout"]:
                    stringBuilder += " --attach stdout " + LINE_END
                if configSection["AttachStderr"]:
                    stringBuilder += " --attach stderr " + LINE_END
                if configSection["Tty"]:
                    stringBuilder += " --tty " + LINE_END
                if configSection["OpenStdin"]:
                    stringBuilder += " --interactive " + LINE_END
                if configSection["Env"]:
                    stringBuilder += ' -e ' + ' -e '.join(configSection["Env"]) + LINE_END
                stringBuilder += " " + image   
                print(stringBuilder)



        except ValueError as e:
            raise SystemExit(e)


if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError as exc:
        sys.exit(exc.errno)
