
# docker-inspect-to-run-parser

  

A simple command line tool that will try to parse the json generated from docker inspect and reverse engineer that to create the docker-run command

  
  

# usage

  

docker inspect **&lt;container&gt;** | python3 parse-docker-inspect.py