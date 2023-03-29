import json
from odoo import _, http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class OpenController(http.Controller):
    _courses_per_page = 2
    # Return a simple string
    @http.route('/hello', auth='public')
    def hello(self):
        return "Hello World"
    
    # Return a simple string with a parameter
    @http.route('/hello/<string:name>', auth='public')
    def hello_name(self, name):
        return "Hello %s" % name
    
    # Rediretion
    @http.route('/test2', auth='public')
    def back_to_web(self):
        return http.redirect_with_hash('/web')
    
    # Return a template
    @http.route(['/courses', '/courses/page/<int:page>'], auth='public', website=True)
    def courses(self, page=0):
        search = request.params.get('search')
        try:
            if search is not None:
                courses = request.env['open_academy.course'].search([('title', 'ilike', search)])
            else:
                courses = request.env['open_academy.course'].search([])  
        except:
            return "<h1>There is an error in the API</h1>"

        total = len(courses)
        pager = request.website.pager(
            url="/courses",
            total=total ,
            page=page,
            step=self._courses_per_page,
            url_args={'search': search} if search else None,
        )
        
        offset = pager ['offset']
        courses = courses [offset: offset + self._courses_per_page]
        return request.render('open_academy_controllers.courses_template', {
            'course': courses.sorted(key=lambda r: r.title),
            'pager': pager,
        })
      
    #Return a template with a parameter  
    @http.route('/course/<int:id>', auth='public', website=True)
    def course(self, id):
        try:
            course = request.env['open_academy.course'].search([('id', '=', id)]) 
        except:
            return "<h1>There is an error in the API</h1>"
        
        return request.render('open_academy_controllers.course_id_template', {
            'course': course,
        })            
        
    @http.route('/courses-json', auth='public')
    def course_json(self):
        try:
            courses = request.env['open_academy.course'].search([])
        except:
            return "<h1>There is an error in the API</h1>"
        
        results = []
        for course in courses:
            results.append({
                'title': course.title,
                'description': course.description,
            })
            
        return request.make_response(json.dumps(results), headers=[('Content-Type', 'application/json')])
        

        
    @http.route(['/my', '/my/home'], auth='public', website=True)
    def my_sessions(self):        
        try:
            user = request.env['res.users'].search([('id', '=', request.session.uid)])
            partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
            sessions = request.env['open_academy.session'].search([('attendees', 'in', partner.id)])
        except:
            return "<h1>There is an error in the API</h1>"
        
        return request.render('open_academy_controllers.sessions_menu', {
            'num_sessions': len(sessions),
        })
        

    @http.route('/course/comment/<int:id>', auth='public', website=True, methods=['POST'])
    def comment(self, id):
        comment = request.params['comment']

        try:
            course = request.env['open_academy.course'].search([('id', '=', id)])
        except:
            return "<h1>There is an error in the API</h1>"
        
        if request.session.uid:
            try:
                user = request.env['res.users'].search([('id', '=', request.session.uid)])
                partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
                c = request.env['mail.message'].create({
                    'model': 'open_academy.course',
                    'res_id': course.id,
                    'body': comment,
                    'message_type': 'comment',
                    'author_id': partner.id,
                })
                course.comments = [(4, c.id)]
            except:
                return "<h1>There is an error adding the comment</h1>"
            
            return http.redirect_with_hash('/course/' + str(course.id))
            
        else:
            return http.redirect_with_hash('/web/login')
        
    @http.route('/course/comment/delete/<int:id>', auth='public', website=True, methods=['POST'])
    def delete_comment(self, id):
        comment_id = request.params['comment_id']
        
        try:
            course = request.env['open_academy.course'].search([('id', '=', id)])
        except:
            return "<h1>There is an error in the API</h1>"
        
        if request.session.uid:
            try:
                c = request.env['mail.message'].search([('id', '=', comment_id)])
                course.comments = [(3, c.id)]
                c.unlink()
            except:
                return "<h1>There is an error deleting the comment</h1>"
            
            return http.redirect_with_hash('/course/' + str(course.id))
            
        else:
            return http.redirect_with_hash('/web/login')
        
    