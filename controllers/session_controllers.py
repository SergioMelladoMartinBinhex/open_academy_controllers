import json
from odoo import _, http
from odoo.http import request

class SessionControllers(http.Controller):
    @http.route('/sessions', auth='public', website=True)
    def sessions(self):
        try:
            user = request.env['res.users'].search([('id', '=', request.session.uid)])
            partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
            sessions = request.env['open_academy.session'].search([('attendees', 'in', partner.id)])
        except:
            return "<h1>There is an error in the API</h1>"
        
        return request.render('open_academy_controllers.sessions_template', {
            'session': sessions.sorted(key=lambda r: r.initial_date),
        })
        
    @http.route('/session/<int:id>', auth='public', website=True)
    def session(self, id):
        try:
            session = request.env['open_academy.session'].search([('id', '=', id)])
        except:
            return "<h1>There is an error in the API</h1>"
        
        joined = False
        if request.session.uid:
            try:
                user = request.env['res.users'].search([('id', '=', request.session.uid)])
                partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
                if partner in session.attendees:
                    joined = True
            except:
                return "<h1>There is an error in the API</h1>"
            
            return request.render('open_academy_controllers.session_id_template', {
                'session': session,
                'joined': joined,
            })
        
        else: 
            return http.redurect_with_hash('/web/login')
        
    @http.route('/sessions-json', auth='public')
    def session_json(self):
        try:
            sessions = request.env['open_academy.session'].search([])
        except:
            return "<h1>There is an error in the API</h1>"
        
        results = []
        for session in sessions:
            results.append({
                'name': session.name,
            })
            
        return request.make_response(json.dumps(results), headers=[('Content-Type', 'application/json')])
    
    @http.route('/join/<int:id>/<string:path>', auth='public', website=True)
    def join_session(self, id, path):
        try:
            session = request.env['open_academy.session'].search([('id', '=', id)])
        except:
            return "<h1>There is an error in the API</h1>"
        
        if request.session.uid:
            try:
                user = request.env['res.users'].search([('id', '=', request.session.uid)])
                partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
                session.attendees = [(4, partner.id)]
            except:
                return "<h1>There is an error adding the user</h1>"
               
            if path == 'course':
                return http.redirect_with_hash('/course/' + str(session.course.id))
            elif path == 'congrats':
                return request.render('open_academy_controllers.joined_session_template', {
                    'session': session,
                })
            else: 
                return http.redirect_with_hash('/my')
            
        else: 
            return http.redirect_with_hash('/web/login')
        
    @http.route('/leave/<int:id>/<string:path>', auth='public', website=True)
    def leave_session(self, id, path):
        try:
            session = request.env['open_academy.session'].search([('id', '=', id)])
        except:
            return "<h1>There is an error in the API</h1>"
        
        if request.session.uid:
            try:
                user = request.env['res.users'].search([('id', '=', request.session.uid)])
                partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
                session.attendees = [(3, partner.id)]
            except:
                return "<h1>There is an error removing the user</h1>"
            
            if path == 'sessions':
                return http.redirect_with_hash('/sessions')
            elif path == 'course':
                return http.redirect_with_hash('/course/' + str(session.course.id))
            else:
                return http.redirect_with_hash('/my/home')
                        
        else: 
            return http.redirect_with_hash('/web/login')
        
    @http.route('/session/comment/<int:id>', auth='public', website=True, methods=['POST'])
    def session_comment(self, id):
        comment = request.params['comment']

        try:
            session = request.env['open_academy.session'].search([('id', '=', id)])
        except:
            return "<h1>There is an error in the API</h1>"
        
        if request.session.uid:
            try:
                user = request.env['res.users'].search([('id', '=', request.session.uid)])
                partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
                c = request.env['mail.message'].create({
                    'model': 'open_academy.session',
                    'res_id': session.id,
                    'body': comment,
                    'message_type': 'comment',
                    'author_id': partner.id,
                })
                session.comments = [(4, c.id)]
            except:
                return "<h1>There is an error adding the comment</h1>"
            
            return http.redirect_with_hash('/session/' + str(session.id))
            
        else:
            return http.redirect_with_hash('/web/login')
        
    @http.route('/session/comment/delete/<int:id>', auth='public', website=True, methods=['POST'])
    def delete_session_comment(self, id):
        comment_id = request.params['comment_id']
        
        try:
            session = request.env['open_academy.session'].search([('id', '=', id)])
        except:
            return "<h1>There is an error in the API</h1>"
        
        if request.session.uid:
            try:
                c = request.env['mail.message'].search([('id', '=', comment_id)])
                session.comments = [(3, c.id)]
                c.unlink()
            except:
                return "<h1>There is an error deleting the comment</h1>"
            
            return http.redirect_with_hash('/session/' + str(session.id))
            
        else:
            return http.redirect_with_hash('/web/login')
