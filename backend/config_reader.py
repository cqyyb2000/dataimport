"""
配置文件读取模块
用于读取set.config配置文件
"""
import configparser
import os
import logging

# 配置文件始终相对本文件所在目录（backend 根），不依赖进程当前工作目录。
# Windows 服务默认 cwd 常为 System32，若仍用相对路径 'set.config' 会读错或失败并触发 app 内 docwebdb 等回退配置。
_BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))


class ConfigReader:
    def __init__(self, config_file=None):
        """初始化配置读取器。

        config_file: 绝对或相对路径；为 None 时优先环境变量 DATAIMPORT_CONFIG_FILE，
        再否则使用与本模块同目录下的 set.config。
        """
        if config_file is None:
            config_file = os.environ.get("DATAIMPORT_CONFIG_FILE")
        if not config_file:
            config_file = os.path.join(_BACKEND_ROOT, "set.config")
        elif not os.path.isabs(config_file):
            config_file = os.path.join(_BACKEND_ROOT, config_file)
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")
        
        try:
            self.config.read(self.config_file, encoding='utf-8')
            print(f"配置文件 {self.config_file} 加载成功")
        except Exception as e:
            raise Exception(f"读取配置文件失败: {str(e)}")
    
    def get_database_config(self):
        """获取数据库配置"""
        try:
            db_config = {
                'host': self.config.get('DATABASE', 'DB_HOST'),
                'port': self.config.getint('DATABASE', 'DB_PORT'),
                'user': self.config.get('DATABASE', 'DB_USER'),
                'password': self.config.get('DATABASE', 'DB_PASSWORD'),
                'database': self.config.get('DATABASE', 'DB_NAME'),
                'charset': self.config.get('DATABASE', 'DB_CHARSET')
            }
            return db_config
        except Exception as e:
            raise Exception(f"读取数据库配置失败: {str(e)}")
    
    def get_database_uri(self):
        """构建数据库连接URI"""
        db_config = self.get_database_config()
        return f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config['charset']}"
    
    def get_security_config(self):
        """获取安全配置"""
        try:
            security_config = {
                'secret_key': self.config.get('SECURITY', 'SECRET_KEY'),
                'jwt_secret_key': self.config.get('SECURITY', 'JWT_SECRET_KEY'),
                'jwt_expires': self.config.getint('SECURITY', 'JWT_ACCESS_TOKEN_EXPIRES')
            }
            return security_config
        except Exception as e:
            raise Exception(f"读取安全配置失败: {str(e)}")
    
    def get_upload_config(self):
        """获取文件上传配置"""
        try:
            upload_config = {
                'upload_folder': self.config.get('UPLOAD', 'UPLOAD_FOLDER'),
                'max_content_length': self.config.getint('UPLOAD', 'MAX_CONTENT_LENGTH'),
                'allowed_extensions': set(self.config.get('UPLOAD', 'ALLOWED_EXTENSIONS').split(',')),
                'upload_path': self.config.get('UPLOAD', 'UPLOAD_PATH'),
                'file_name_length': self.config.getint('UPLOAD', 'FILE_NAME_LENGTH'),
                'upload_timeout': self.config.getint('UPLOAD', 'UPLOAD_TIMEOUT')
            }
            return upload_config
        except Exception as e:
            raise Exception(f"读取上传配置失败: {str(e)}")
    
    def get_application_config(self):
        """获取应用配置"""
        try:
            app_config = {
                'debug': self.config.getboolean('APPLICATION', 'DEBUG'),
                'host': self.config.get('APPLICATION', 'HOST'),
                'port': self.config.getint('APPLICATION', 'PORT'),
                'threaded': self.config.getboolean('APPLICATION', 'THREADED')
            }
            return app_config
        except Exception as e:
            raise Exception(f"读取应用配置失败: {str(e)}")
    
    def get_logging_config(self):
        """获取日志配置"""
        try:
            logging_config = {
                'log_level': self.config.get('LOGGING', 'LOG_LEVEL'),
                'log_file': self.config.get('LOGGING', 'LOG_FILE'),
                'log_max_size': self.config.getint('LOGGING', 'LOG_MAX_SIZE'),
                'log_backup_count': self.config.getint('LOGGING', 'LOG_BACKUP_COUNT')
            }
            return logging_config
        except Exception as e:
            raise Exception(f"读取日志配置失败: {str(e)}")
    
    def get(self, section, option, fallback=None):
        """通用配置获取方法"""
        try:
            return self.config.get(section, option, fallback=fallback)
        except Exception:
            return fallback
    
    def getint(self, section, option, fallback=None):
        """获取整数配置"""
        try:
            return self.config.getint(section, option, fallback=fallback)
        except Exception:
            return fallback
    
    def getboolean(self, section, option, fallback=None):
        """获取布尔值配置"""
        try:
            return self.config.getboolean(section, option, fallback=fallback)
        except Exception:
            return fallback

# 创建全局配置实例
try:
    config_reader = ConfigReader()
except Exception as e:
    print(f"配置文件加载失败: {str(e)}")
    config_reader = None 