import os
import configparser
import sys, getopt
import logging
import os.path
from .client import create_client
from .server import run as server_run
import asyncio
import json

logger = logging.getLogger(__name__)


def usage():
    print('python -m okws.server -c <configfile>')
    exit(1)


def read_config(config_file):
    logger.info(f"config file: {config_file}")
    if os.path.isfile(config_file) and os.access(config_file, os.R_OK):
        conf = configparser.ConfigParser()
        conf.read(config_file, encoding='utf-8')
        # sections = conf.sections()
        return conf
    else:
        logger.error(f"{config_file} 文件不存在或不可读")
        exit(1)


def parse_argv(argv):
    try:
        opts, args = getopt.getopt(argv[1:], "-h-c:", ['help'])
    except getopt.GetoptError:
        usage()
    for opt, arg in opts:
        if opt in ("-c"):
            return read_config(arg)
        else:
            usage()


async def start_websockets(config):
    if config is None:
        # 没有配置文件
        return
    okex = await create_client()
    await asyncio.sleep(2)
    for section in config.sections():
        if section != 'config':
            logger.info(f"启动 {section}")
            params = dict(config[section])
            # logger.info(params['commands'])
            ret = await okex.open_ws(section, params)
            logger.info(ret)

            # send command to websocket if exist
            commands = params.get('commands')
            if commands is not None:
                await asyncio.sleep(2)
                commands = commands.strip().splitlines()
                for command in commands:
                    try:
                        cmd = json.loads(command)
                        cmd['name'] = section
                        # logger.info(f"发送命令:{command}")
                        await okex.send(cmd)
                    except Exception:
                        logger.warning(f"错误命令：{command}")

    ret = await okex.servers()
    logger.info(f"{ret['message']} 已启动")


async def run(config):
    await asyncio.gather(
        server_run(),
        start_websockets(config)
    )


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(filename)s[%(lineno)d] - %(levelname)s: %(message)s')
    config = parse_argv(sys.argv)
    asyncio.run(run(config))
