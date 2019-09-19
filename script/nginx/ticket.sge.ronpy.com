server {
    charset              utf-8;
    listen               80;
    listen               443 ssl;
    server_name          ticket.sge.ronpy.com ticket.sge-tech.com;

    ssl_certificate      /etc/nginx/ssl/ticket.sge.ronpy.com/fullchain.cer;
    ssl_certificate_key  /etc/nginx/ssl/ticket.sge.ronpy.com/ticket.sge.ronpy.com.key;
    ssl_protocols        TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers          HIGH:!aNULL:!MD5;

    location / {
        proxy_pass_header Server;
        proxy_pass        http://127.0.0.1:10000;
        proxy_redirect    off;
        proxy_set_header  Host $host;
        proxy_set_header  X-Real-IP $host;
        proxy_set_header  X-Scheme $scheme;
        proxy_set_header  X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header  Cookie $http_cookie;
        proxy_buffering   off;
    }
}
