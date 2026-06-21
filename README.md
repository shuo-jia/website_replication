# 股票资讯网站项目
## 简介
本项目只是对某个网站的模仿。

主要实现了：新闻资讯、股票数据抓取，数据保存和页面展示；附带简单的用户注册、登
录、登出功能。

本项目使用 Python 完成，使用了后端框架 Django，前端页面则通过 Django 的模板 +
`bootstrap4` + `echarts`来完成。本项目不包含`bootstrap4`、`echarts`源码，这些依
赖均通过`CDN`加载。新闻资讯从网页抓取，股票数据则通过`akshare`获取。

## 部署
本项目仅尝试部署在 Debian 上，使用 uWSGI + Nginx + Mariadb 的组合。

在开始下面的步骤之前，将代码复制到`/var/www/`下。

### 安装依赖
Django 默认使用 Sqlite，本项目在开发时使用 Sqlite，而在部署时使用 Mariadb。安装
Mariadb：
```
sudo apt install mariadb-server
```
除此之外，Django 还需安装 mysqlclient，这将在之后进行。现在来安装 mysqlclient 的
一些[依赖](https://pypi.org/project/mysqlclient/)：
```
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config
```
项目部署还使用了 Nginx，安装命令如下：
```
sudo apt install nginx
```
现在来安装其他 Python 包，包括 Django、uWSGI、mysqlclient 等依赖：
```
# 安装 python3-venv
sudo apt install python3-venv
# 进入项目根目录，创建虚拟环境
mkdir .venv
python3 -m venv .venv
# 安装依赖
.venv/bin/pip3 install -r requirements.txt  --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 数据库配置
在 Mariadb 中创建数据库：
```
CREATE DATABASE <dbname> CHARACTER SET utf8mb4;
```
本项目在`./config/settings.py`的`DATABASES`设置中，通过读取项目根目录下的
`stock.cnf`文件来配置数据库用户名和密码，部署时应增加此配置文件，其形如：
```
# stock.cnf
[client]
database = NAME
user = USER
password = PASSWORD
default-character-set = utf8mb4
```
创建配置文件后，执行如下命令以创建数据库表格：
```
.venv/bin/python3 manage.py makemigrations user
.venv/bin/python3 manage.py makemigrations news
.venv/bin/python3 manage.py makemigrations stock
.venv/bin/python3 manage.py migrate
```

### Nginx 配置
现在，在目录`/etc/nginx/sites-available/`中创建文件`website_replication.conf`，
内容如下：
```
# 用于 Django 网站
# the upstream component nginx needs to connect to
upstream django {
    server unix:///run/uwsgi/website_replication.sock;
}

# configuration of the server
server {
    # the port your site will be served on
    listen      8000;
    # the domain name it will serve for
    # server_name example.com; # substitute your machine's IP address or FQDN
    server_name 127.0.0.1;
    charset     utf-8;

    # max upload size
    client_max_body_size 75M;   # adjust to taste

    location /static {
        # your Django project's static files - amend as required
        alias /var/www/website_replication/static_root/;
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        uwsgi_pass  django;
        include     /etc/nginx/uwsgi_params;
    }
}
```
作为测试，这里`server`的`server_name`设置为了本机地址。

接下来需将此配置使能，如
```
sudo ln -s /etc/nginx/sites-available/website_replication.conf /etc/nginx/sites-enabled/
```
最后重启 Nginx。

### Django 配置
首先来迁移静态文件。
运行
```
.venv/bin/python3 manage.py collectstatic
```

部署时，应当运行：
```
.venv/bin/python3 manage.py  check --deploy
```
这会检查配置中的安全问题，并给出提示。在`settings.py`中有如下选项需修改：
- 将`DEBUG`设置为 False；
- 设置`ALLOWED_HOSTS`，如在本地使用，可设置为
  ```
  ALLOWED_HOSTS = ["localhost", "127.0.0.1",]
  ```
- 设置`SESSION_COOKIE_SECURE`为 True；
- 设置`CSRF_COOKIE_SECURE`为 True；
- 重新设置`SECRET_KEY`，可通过如下方式生成：
  ```
  ./.venv/bin/python3 manage.py shell
  from django.core.management.utils import get_random_secret_key
  print(get_random_secret_key())
  ```

### uWSGI 配置
设置开机自启动 uWSGI，并且将 uWSGI 的配置写入配置文件。注意这里将不考虑给所有用
户 socket 的读写权限，而是修改其所属用户为`www-data`（这是 Debian 中 Nginx 的用
户名）。

首先在项目中创建`uwsgi.ini`，其内容如下：
```
[uwsgi]

# Django-related settings the base directory (full path)
chdir           = /var/www/website_replication
# Django's wsgi file
module          = config.wsgi
# the virtualenv (full path)
home            = /var/www/website_replication/.venv

# process-related settings
# master
master          = true
pidfile = /run/uwsgi/uwsgi.pid
# maximum number of worker processes
processes       = 10
# the socket (use the full path to be safe
socket          = /run/uwsgi/website_replication.sock
# ... with appropriate permissions - may be needed
chmod-socket    = 664
chown-socket = www-data:www-data
# clear environment on exit
vacuum          = true
```
这里设置了`pidfile`和`socket`，其中`pidfile`可用于关闭 uWSGI，`socket`供 Nginx
使用。

接着创建`/etc/systemd/system/uwsgi.service`文件，其内容为
```
[Unit]
Description=uWSGI for website_replication
After=network.target

[Service]
User=www-data
Group=www-data
RuntimeDirectory=uwsgi
ExecStart=/var/www/website_replication/.venv/bin/uwsgi \
	--ini /var/www/website_replication/uwsgi.ini
ExecStop=/var/www/website_replication/.venv/bin/uwsgi --stop /run/uwsgi/uwsgi.pid
Restart=always

[Install]
WantedBy=multi-user.target
```

执行如下命令启动服务：
```
sudo systemctl daemon-reload
sudo systemctl enable uwsgi
sudo systemctl start uwsgi
```
执行如下命令停止服务：
```
sudo systemctl stop uwsgi
```
此时应可通过浏览器访问。

### 自动拉取数据
对于本项目，还有最后一步要做，就是自动更新数据库。在本项目下，提供了
`update.py`脚本，此脚本可用于更新数据库数据。部分历史数据在用户点击链接时自动拉
取，而对于一些实时的股票数据、新闻资讯，可使用命令：
```
./.venv/bin/python3 update.py --news
./.venv/bin/python3 update.py --stock
```
来更新。除此之外，还需要手动更新 K 线数据，这应在当日股市收盘并且执行了
`./.venv/bin/python3 update.py --stock`之后才能执行：
```
./.venv/bin/python3 update.py --history-price
```
这一任务可通过`crontab`定时工具实现，此处不再详细给出。
