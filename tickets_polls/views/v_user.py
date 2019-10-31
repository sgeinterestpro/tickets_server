#!/usr/bin/env python3
# encoding: utf-8

"""
@Time    : 2019/7/11 16:52
@Author  : Sam
@Email   : muumlover@live.com
@Blog    : https://blog.muumlover.com
@Project : tickets_server
@FileName: v_user.py
@Software: PyCharm
@license : (C) Copyright 2019 by muumlover. All rights reserved.
@Desc    : 

"""
import uuid
from datetime import datetime

from aiohttp import web
from aiohttp.abc import Request, StreamResponse
from bson import ObjectId

from model import User, UserInit, Captcha
from u_email import EmailSender
from unit import get_sport


def msg(url):
    return f'''<style class="fox_global_style">
    div.fox_html_content {{ line-height: 1.5; }}
    /* 一些默认样式 */
    blockquote {{ margin-Top: 0px; margin-Bottom: 0px; margin-Left: 0.5em }}
    ol, ul {{ margin-Top: 0px; margin-Bottom: 0px; list-style-position: inside; }}
    p {{ margin-Top: 0px; margin-Bottom: 0px }}
</style>
<table border="0" cellpadding="0" cellspacing="0" width="100%">
    <tbody><tr><td bgcolor="#f7f9fa" align="center" style="padding:22px 0 20px 0" class="responsive-table">
        <table border="0" cellpadding="0" cellspacing="0" style="background-color:f7f9fa; border-radius:3px;border:1px solid #dedede;margin:0 auto; background-color:#ffffff" width="552" class="responsive-table">
            <tbody><tr><td bgcolor="#ffffff" height="54" align="center" style="border-top-left-radius:3px;border-top-right-radius:3px;border-bottom-width: 1px;border-bottom-style: solid;border-bottom-color: #dedede;">
                <table border="0" cellpadding="0" cellspacing="0" width="100%"><tbody><tr>
                    <td align="center" class="zhwd-high-res-img-wrap zhwd-zhihu-logo">
                        <img src="https://www.sge.com.cn/static/images/logo.png" width="198" height="46" alt="SGE" style="outline:none; display:block; border:none; font-size:14px; font-family:Hiragino Sans GB; color:#ffffff;"></a>
                    </td>
                </tr></tbody></table>
            </td></tr>
            <tr><td bgcolor="#ffffff" align="center" style="padding: 0 15px 0px 15px;">
                <table border="0" cellpadding="0" cellspacing="0" width="480" class="responsive-table">
                    <tbody><tr><td><table width="100%" border="0" cellpadding="0" cellspacing="0">
                        <tbody><tr><td><table cellpadding="0" cellspacing="0" border="0" align="left" class="responsive-table">
                            <tbody><tr><td width="550" align="left" valign="top">
                                <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                    <tbody>
                                    <tr>
                                        <td bgcolor="#ffffff" align="left" style="background-color:#ffffff; font-size: 17px; color:#7b7b7b; padding:28px 0 0 0;line-height:25px;">
                                            <b>您好!</b>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td align="left" valign="top" style="font-size:15px; color:#7b7b7b; font-size:14px; line-height: 25px; font-family:Hiragino Sans GB; padding: 20px 0px 20px 0px">
                                            感谢您使用本程序,请点击以下链接绑定帐号:
                                        </td>
                                    </tr>
                                    <tr><td style="border-bottom:1px #f1f4f6 solid; padding: 10px 0 35px 0;" align="center" class="padding">
                                        <table border="0" cellspacing="0" cellpadding="0" class="responsive-table">
                                            <tbody>
                                            <tr>
                                                <td>
                                                    <span style="font-family:Hiragino Sans GB;font-size:17px;">
                                                        <a style="text-decoration:none;color:#ffffff;"
                                                           href="{url}"
                                                           target="_blank">
                                                            <div style="padding:10px 25px 10px 25px;border-radius:3px;text-align:center;text-decoration:none;background-color:#0a82e4;color:#ffffff;font-size:17px;margin:0;white-space:nowrap">
                                                                立即绑定帐号
                                                            </div>
                                                        </a>
                                                    </span>
                                                </td>
                                            </tr>
                                            </tbody>
                                        </table>
                                    </td></tr>
                                    <tr>
                                        <td align="left" valign="top" style="font-size:15px; color:#7b7b7b; font-size:14px; line-height: 25px; font-family:Hiragino Sans GB; padding: 20px 0px 35px 0px">
                                            如果以上按钮无法打开，请把下面的链接复制到浏览器地址栏中打开：{url}
                                        </td>
                                    </tr>
                                    </tbody>
                                </table>
                            </td>
                            </tr>
                            </tbody>
                        </table>
                        </td>
                        </tr>
                        </tbody>
                    </table>
                    </td>
                    </tr>
                    </tbody>
                </table>
            </td>
            </tr>
            </tbody>
        </table>
    </td>
    </tr>
    </tbody>
</table>
'''


class UserHandles:

    @staticmethod
    async def user_info(request: Request) -> StreamResponse:

        user_info = {}
        user = await User.find_or_insert_one({'wx_open_id': request['open-id']})
        user_init = await UserInit.m_find_one_by_user(user)
        if user_init is not None:
            user_info.update(user_init.to_json())
        user_info.update(user.to_json())
        user_info['sports'] = get_sport()
        return web.json_response({'code': 0, 'message': '获取用户信息成功', 'data': user_info})

    @staticmethod
    async def user_update(request: Request) -> StreamResponse:

        data = await request.json()
        if 'userInfo' not in data:
            return web.json_response({'code': -2, 'message': '用户信息不存在'})
        user = await User.find_or_insert_one({'wx_open_id': request['open-id']})
        _ = await User.update_one(user.to_object(), {
            '$set': data['userInfo']
        })
        return web.json_response({'code': 0, 'message': '同步用户信息成功'})

    @staticmethod
    async def user_bind(request: Request) -> StreamResponse:

        user = await User.find_one({'wx_open_id': request['open-id']})
        data = await request.json()

        if user['init_id']:
            return web.json_response({'code': -1, 'message': '该微信已经绑定了其他邮箱'})

        user_init = await UserInit.find_one({'email': data['email']})
        if not user_init:
            return web.json_response({'code': -1, 'message': '该邮箱非组织内部人员邮箱'})

        count = await User.count({'email': data['email']})
        if count > 0:
            return web.json_response({'code': -1, 'message': '该邮箱已经绑定了其他微信'})

        random_code = uuid.uuid1().hex
        url = request.app.router['email-check'].url_for(uuid=random_code)
        final_url = f'{request.url.parent}{url}'

        _ = await Captcha.insert_one({
            'captcha': random_code,
            'email': data['email'],
            'user_id': user.mongo_id,
            'url': final_url,
            'expire_time': datetime.utcnow()
        })

        # noinspection PyBroadException
        try:
            await EmailSender.send(
                data['email'], '票券小程序账号绑定验证邮件',
                msg(final_url)
            )

            return web.json_response({'code': 0, 'message': '邮件发送成功'})
        except Exception:
            return web.json_response({'code': -3, 'message': '邮件服务器繁忙'})

    @staticmethod
    async def member_add(request: Request) -> StreamResponse:

        data = await request.json()

        if 'real_name' not in data or not data['real_name']:
            return web.json_response({'code': -2, 'message': '姓名不能为空'})
        if 'work_no' not in data or not data['work_no']:
            return web.json_response({'code': -2, 'message': '工号不能为空'})
        if 'email' not in data or not data['email']:
            return web.json_response({'code': -2, 'message': '电子邮件不能为空'})
        if 'phone' not in data or not data['phone']:
            return web.json_response({'code': -2, 'message': '手机号码不能为空'})
        if 'sports' not in data or not data['sports']:
            return web.json_response({'code': -2, 'message': '运动项目不能为空'})
        if 'role' not in data or not data['role']:
            return web.json_response({'code': -2, 'message': '用户角色不能为空'})

        res = await UserInit.insert_one(data)
        if res.inserted_id is None:
            return web.json_response({'code': -3, 'message': '保存用户数据失败'})

        return web.json_response({'code': 0, 'message': '添加用户成功'})

    @staticmethod
    async def member_delete(request: Request) -> StreamResponse:

        data = await request.json()
        if 'init_id' not in data:
            return web.json_response({'code': -1, 'message': '请求参数错误'})

        user = await User.find_one({'wx_open_id': request['open-id']})
        if data['init_id'] == str(user['init_id']):
            return web.json_response({'code': -1, 'message': '无法删除正在使用的账号'})

        res = await UserInit.delete_one({'_id': ObjectId(data['init_id'])})
        if res.deleted_count == 0:
            return web.json_response({'code': -3, 'message': '删除用户数据失败'})

        return web.json_response({'code': 0, 'message': '删除用户成功'})

    @staticmethod
    async def member_find(request: Request) -> StreamResponse:

        data = await request.json()
        if 'init_id' not in data:
            return web.json_response({'code': -1, 'message': '请求参数错误'})

        user = await User.find_one({'wx_open_id': request['open-id']})
        user_init = await UserInit.m_find_one_by_user(user)

        if 'admin' not in user_init['role']:
            return web.json_response({'code': -1, 'message': '没有相应权限'})

        user_info = {}

        t_user_init = await UserInit.find_one({'_id': ObjectId(data['init_id'])})

        t_user = await User.find_one({'init_id': t_user_init.mongo_id})
        if t_user is not None:
            user_info.update(t_user.to_json())
            user_info['user_id'] = user_info.pop('_id')

        user_info.update(t_user_init.to_json())
        user_info['init_id'] = user_info.pop('_id')

        return web.json_response({'code': 0, 'message': '获取用户信息成功', 'data': user_info})

    @staticmethod
    async def member_list(request: Request) -> StreamResponse:

        cursor = UserInit.find()

        count, items = 0, []
        # for ticket in await cursor.to_list(length=100):
        async for user_init in cursor:
            user_info = {}

            t_user = await User.find_one({'init_id': user_init.mongo_id})
            if t_user is not None:
                user_info.update(t_user.to_json())
                user_info['user_id'] = user_info.pop('_id')

            user_info.update(user_init.to_json())
            user_info['init_id'] = user_info.pop('_id')

            items.append(user_info)
            count += 1

        return web.json_response({'code': 0, 'message': '获取用户列表成功', 'count': count, 'items': items})
