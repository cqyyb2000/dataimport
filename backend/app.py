from flask import Flask
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from Model.dataCls import db
from routes.users import users_bp
from routes.menus import menus_bp
from routes.permissions import permission_bp
from routes.account_book import account_book_bp
from routes.share_upload import share_upload_bp
from routes.gl_upload import gl_upload_bp
from routes.custom_archive import custom_archive_bp
from routes.vouchers import vouchers_bp
from routes.gl_account_balance import gl_account_balance_bp
from routes.accounts import accounts_bp
from routes.bx import bx_bp
from config_reader import config_reader

# 加载环境变量（与 set.config 一样锚定 backend 目录，避免服务进程 cwd 非项目目录时读到别处）
_backend_root = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_backend_root, ".env"))

# 创建Flask应用
app = Flask(__name__)

# 从配置文件加载配置
if config_reader:
    try:
        # 数据库配置
        app.config['SQLALCHEMY_DATABASE_URI'] = config_reader.get_database_uri()
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # 安全配置
        security_config = config_reader.get_security_config()
        app.config['SECRET_KEY'] = security_config['secret_key']
        app.config['JWT_SECRET_KEY'] = security_config['jwt_secret_key']
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = security_config['jwt_expires']
        
        # 文件上传配置
        upload_config = config_reader.get_upload_config()
        app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), upload_config['upload_folder'])
        app.config['MAX_CONTENT_LENGTH'] = upload_config['max_content_length']
        app.config['ALLOWED_EXTENSIONS'] = upload_config['allowed_extensions']
        app.config['UPLOAD_PATH'] = upload_config['upload_path']
        app.config['FILE_NAME_LENGTH'] = upload_config['file_name_length']
        app.config['UPLOAD_TIMEOUT'] = upload_config['upload_timeout']
        
        # 应用配置
        app_config = config_reader.get_application_config()
        app.config['DEBUG'] = app_config['debug']
        
        print("配置文件加载成功")
        
    except Exception as e:
        print(f"配置文件加载失败，使用默认配置: {str(e)}")
        # 回退到默认配置
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI', 'mysql+pymysql://root:cqyyb031125@localhost/docwebdb')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'key031125')
        app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
        app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
        app.config['UPLOAD_PATH'] = 'uploads'
        app.config['FILE_NAME_LENGTH'] = 255
        app.config['UPLOAD_TIMEOUT'] = 300
else:
    print("配置读取器未初始化，使用默认配置")
    # 使用默认配置
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI', 'mysql+pymysql://root:cqyyb031125@localhost/docwebdb')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'key031125')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
    app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    app.config['UPLOAD_PATH'] = 'uploads'
    app.config['FILE_NAME_LENGTH'] = 255
    app.config['UPLOAD_TIMEOUT'] = 300

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化数据库
db.init_app(app)

# 允许跨域访问
CORS(app)

# 注册蓝图
app.register_blueprint(users_bp)
app.register_blueprint(menus_bp)
app.register_blueprint(permission_bp)
app.register_blueprint(account_book_bp)
app.register_blueprint(share_upload_bp)
app.register_blueprint(gl_upload_bp)
app.register_blueprint(custom_archive_bp)
app.register_blueprint(vouchers_bp)
app.register_blueprint(gl_account_balance_bp)
app.register_blueprint(accounts_bp)
app.register_blueprint(bx_bp)


def setup_logging():
    """设置日志配置"""
    if config_reader:
        try:
            logging_config = config_reader.get_logging_config()
            
            # 创建日志目录
            log_dir = os.path.dirname(logging_config['log_file'])
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # 设置日志级别
            log_level = getattr(logging, logging_config['log_level'].upper(), logging.INFO)
            
            # 配置日志处理器
            handler = RotatingFileHandler(
                logging_config['log_file'],
                maxBytes=logging_config['log_max_size'],
                backupCount=logging_config['log_backup_count'],
                encoding='utf-8'
            )
            
            formatter = logging.Formatter(
                '%(asctime)s %(levelname)s %(name)s %(message)s'
            )
            handler.setFormatter(formatter)
            
            # 设置应用日志
            app.logger.setLevel(log_level)
            app.logger.addHandler(handler)
            
            print(f"日志配置成功: {logging_config['log_file']}")
            
        except Exception as e:
            print(f"日志配置失败: {str(e)}")

if __name__ == '__main__':
    # 设置日志
    setup_logging()
    
    # 获取应用配置
    if config_reader:
        try:
            app_config = config_reader.get_application_config()
            app.run(
                debug=app_config['debug'],
                host=app_config['host'],
                port=app_config['port'],
                threaded=app_config['threaded']
            )
        except Exception as e:
            print(f"使用配置文件启动失败，使用默认配置: {str(e)}")
            app.run(debug=True)
    else:
        print("使用默认配置启动应用")
        app.run(debug=True)