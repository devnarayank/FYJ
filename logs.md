[22:11:44] DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 404, b'Not Found',            
                    [(b'Content-Type', b'text/plain; charset=utf-8'), (b'Content-Length', b'15'),              
                    (b'Connection', b'keep-alive'), (b'Date', b'Wed, 02 Sep 2026 16:41:44 GMT'), (b'ETag',     
                    b'W/"f-mY2VvLxuxB7KhsoOdQTlMTccuAQ"'), (b'X-Powered-By', b'huggingface-moon'),             
                    (b'X-Request-Id',                                                                          
                    b'Root=1-6a9851c8-0b4f83d170367d3b54ee6545;1ed8e7c4-7e48-40f6-b107-8bfe5c5c6d37'),         
                    (b'RateLimit', b'"resolvers";r=2988;t=174'), (b'RateLimit-Policy', b'"fixed                
                    window";"resolvers";q=3000;w=300'), (b'cross-origin-opener-policy', b'same-origin'),       
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'), (b'Vary',          
                    b'Origin'), (b'Access-Control-Expose-Headers',                                             
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Repo-Commit',            
                    b'1110a243fdf4706b3f48f1d95db1a4f5529b4d41'), (b'Accept-Ranges', b'bytes'),                
                    (b'X-HF-Warning', b'unauthenticated; Warning: You are sending unauthenticated requests to  
                    the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.'),    
                    (b'X-Hub-Cache', b'MISS'), (b'X-Error-Code', b'EntryNotFound'), (b'X-Error-Message',       
                    b'Entry not found'), (b'X-Cache', b'Error from cloudfront'), (b'Via', b'1.1                
                    e4257444e1baa2e44ac1a48dd385109c.cloudfront.net (CloudFront)'), (b'X-Amz-Cf-Pop',          
                    b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'), (b'X-Amz-Cf-Id',                       
                    b'IXwbobc0oyW5o9f8cqWBoFAXRFMCrO381QYCT0Y5ZDQ-G9FuQLvCrw=='),                              
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'HEAD']>                                  
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'HEAD']>                                   
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'HEAD']>                                      
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'HEAD']>                               
           DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 307, b'Temporary Redirect',   
                    [(b'Content-Type', b'text/plain; charset=utf-8'), (b'Content-Length', b'300'),             
                    (b'Connection', b'keep-alive'), (b'Date', b'Wed, 02 Sep 2026 16:41:44 GMT'), (b'Location', 
                    b'/api/resolve-cache/models/sentence-transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d9
                    5db1a4f5529b4d41/tokenizer_config.json?%2Fsentence-transformers%2Fall-MiniLM-L6-v2%2Fresolv
                    e%2Fmain%2Ftokenizer_config.json=&etag=%22c79f2b6a0cea6f4b564fed1938984bace9d30ff0%22'),   
                    (b'X-Powered-By', b'huggingface-moon'), (b'X-Request-Id',                                  
                    b'Root=1-6a9851c8-6fb3e4fe140d7c43752c2cb2;4e231425-f63f-4c90-812c-d0b741cef752'),         
                    (b'RateLimit', b'"resolvers";r=2987;t=174'), (b'RateLimit-Policy', b'"fixed                
                    window";"resolvers";q=3000;w=300'), (b'cross-origin-opener-policy', b'same-origin'),       
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'), (b'Vary', b'Origin,
                    Accept'), (b'Access-Control-Expose-Headers',                                               
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Repo-Commit',            
                    b'1110a243fdf4706b3f48f1d95db1a4f5529b4d41'), (b'Accept-Ranges', b'bytes'),                
                    (b'X-HF-Warning', b'unauthenticated; Warning: You are sending unauthenticated requests to  
                    the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.'),    
                    (b'X-Hub-Cache', b'HIT'), (b'Content-Disposition', b'inline;                               
                    filename*=UTF-8\'\'tokenizer_config.json; filename="tokenizer_config.json";'),             
                    (b'Content-Security-Policy', b"default-src 'none'; sandbox"), (b'X-Linked-ETag',           
                    b'"c79f2b6a0cea6f4b564fed1938984bace9d30ff0"'), (b'X-Cache', b'Miss from cloudfront'),     
                    (b'Via', b'1.1 e4257444e1baa2e44ac1a48dd385109c.cloudfront.net (CloudFront)'),             
                    (b'X-Amz-Cf-Pop', b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'), (b'X-Amz-Cf-Id',     
                    b'HntRiFKYi5CNCwfdSALevTpl_odMgT_NV_quoibh9GcD9T4K3MaXvw=='),                              
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'HEAD']>                                  
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'HEAD']>                                   
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'HEAD']>                                      
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'HEAD']>                               
           DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Content-Type',
                    b'text/plain; charset=utf-8'), (b'Content-Length', b'350'), (b'Connection', b'keep-alive'),
                    (b'Date', b'Mon, 10 Aug 2026 11:50:52 GMT'), (b'ETag',                                     
                    b'"c79f2b6a0cea6f4b564fed1938984bace9d30ff0"'), (b'X-Powered-By', b'huggingface-moon'),    
                    (b'X-Request-Id',                                                                          
                    b'Root=1-6a79bb1c-192c760b515b263862a57810;7ffbcb83-1f07-4d9f-8225-04de3c268839'),         
                    (b'RateLimit', b'"resolvers";r=2987;t=76'), (b'RateLimit-Policy', b'"fixed                 
                    window";"resolvers";q=3000;w=300'), (b'cross-origin-opener-policy', b'same-origin'),       
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'),                    
                    (b'Access-Control-Expose-Headers',                                                         
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Repo-Commit',            
                    b'1110a243fdf4706b3f48f1d95db1a4f5529b4d41'), (b'Accept-Ranges', b'bytes'),                
                    (b'Content-Disposition', b'inline; filename*=UTF-8\'\'tokenizer_config.json;               
                    filename="tokenizer_config.json";'), (b'Content-Security-Policy', b"default-src 'none';    
                    sandbox"), (b'Vary', b'Origin'), (b'X-Cache', b'Hit from cloudfront'), (b'Via', b'1.1      
                    e4257444e1baa2e44ac1a48dd385109c.cloudfront.net (CloudFront)'), (b'X-Amz-Cf-Pop',          
                    b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'), (b'X-Amz-Cf-Id',                       
                    b'NrbI1FLSM0BiK5APNSfiV12U8GttmMwhnyGYgzs-16TTFU86_YYP5Q=='), (b'Age', b'2004652'),        
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'HEAD']>                                  
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'HEAD']>                                   
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'HEAD']>                                      
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'HEAD']>                               
[22:11:45] DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 307, b'Temporary Redirect',   
                    [(b'Content-Type', b'text/plain; charset=utf-8'), (b'Content-Length', b'280'),             
                    (b'Connection', b'keep-alive'), (b'Date', b'Wed, 02 Sep 2026 16:41:44 GMT'), (b'Location', 
                    b'/api/resolve-cache/models/sentence-transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d9
                    5db1a4f5529b4d41/config.json?%2Fsentence-transformers%2Fall-MiniLM-L6-v2%2Fresolve%2Fmain%2
                    Fconfig.json=&etag=%2272b987fd805cfa2b58c4c8c952b274a11bfd5a00%22'), (b'X-Powered-By',     
                    b'huggingface-moon'), (b'X-Request-Id',                                                    
                    b'Root=1-6a9851c8-59d4dd261cec5e85216dc789;38c2e9bf-dd23-45ab-8461-c68be80aab66'),         
                    (b'RateLimit', b'"resolvers";r=2986;t=174'), (b'RateLimit-Policy', b'"fixed                
                    window";"resolvers";q=3000;w=300'), (b'cross-origin-opener-policy', b'same-origin'),       
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'), (b'Vary', b'Origin,
                    Accept'), (b'Access-Control-Expose-Headers',                                               
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Repo-Commit',            
                    b'1110a243fdf4706b3f48f1d95db1a4f5529b4d41'), (b'Accept-Ranges', b'bytes'),                
                    (b'X-HF-Warning', b'unauthenticated; Warning: You are sending unauthenticated requests to  
                    the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.'),    
                    (b'X-Hub-Cache', b'HIT'), (b'Content-Disposition', b'inline;                               
                    filename*=UTF-8\'\'config.json; filename="config.json";'), (b'Content-Security-Policy',    
                    b"default-src 'none'; sandbox"), (b'X-Linked-ETag',                                        
                    b'"72b987fd805cfa2b58c4c8c952b274a11bfd5a00"'), (b'X-Cache', b'Miss from cloudfront'),     
                    (b'Via', b'1.1 e4257444e1baa2e44ac1a48dd385109c.cloudfront.net (CloudFront)'),             
                    (b'X-Amz-Cf-Pop', b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'), (b'X-Amz-Cf-Id',     
                    b'J3V0gZ3-ErNah1OniRFXFh4XDAs3xbCLqE5eEyavks-a6sRtMgF7Xw=='),                              
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'HEAD']>                                  
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'HEAD']>                                   
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'HEAD']>                                      
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'HEAD']>                               
           DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Content-Type',
                    b'text/plain; charset=utf-8'), (b'Content-Length', b'612'), (b'Connection', b'keep-alive'),
                    (b'Date', b'Mon, 01 Jun 2026 06:29:13 GMT'), (b'ETag',                                     
                    b'"72b987fd805cfa2b58c4c8c952b274a11bfd5a00"'), (b'X-Powered-By', b'huggingface-moon'),    
                    (b'X-Request-Id',                                                                          
                    b'Root=1-6a1d26b9-6cedbb9e6ebe2dae066c5d2c;a2c7e532-0dc7-4ea3-8085-aa1fbd025327'),         
                    (b'RateLimit', b'"resolvers";r=2770;t=197'), (b'RateLimit-Policy', b'"fixed                
                    window";"resolvers";q=3000;w=300'), (b'cross-origin-opener-policy', b'same-origin'),       
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'),                    
                    (b'Access-Control-Expose-Headers',                                                         
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Repo-Commit',            
                    b'1110a243fdf4706b3f48f1d95db1a4f5529b4d41'), (b'Accept-Ranges', b'bytes'),                
                    (b'X-Hub-Cache', b'MISS'), (b'Content-Disposition', b'inline;                              
                    filename*=UTF-8\'\'config.json; filename="config.json";'), (b'Content-Security-Policy',    
                    b"default-src 'none'; sandbox"), (b'Vary', b'Origin'), (b'X-Cache', b'Hit from             
                    cloudfront'), (b'Via', b'1.1 e4257444e1baa2e44ac1a48dd385109c.cloudfront.net               
                    (CloudFront)'), (b'X-Amz-Cf-Pop', b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'),      
                    (b'X-Amz-Cf-Id', b'Ssf4duB62OteVUpWKHrt1JbWRH8NGJpazl_dvg5fRTylyBzQyl1HdA=='), (b'Age',    
                    b'8071952'), (b'Strict-Transport-Security', b'max-age=31536000')])                         
           DEBUG    receive_response_body.started request=<Request [b'HEAD']>                                  
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'HEAD']>                                   
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'HEAD']>                                      
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'HEAD']>                               
[22:11:46] DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 307, b'Temporary Redirect',   
                    [(b'Content-Type', b'text/plain; charset=utf-8'), (b'Content-Length', b'280'),             
                    (b'Connection', b'keep-alive'), (b'Date', b'Wed, 02 Sep 2026 16:41:45 GMT'), (b'Location', 
                    b'/api/resolve-cache/models/sentence-transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d9
                    5db1a4f5529b4d41/config.json?%2Fsentence-transformers%2Fall-MiniLM-L6-v2%2Fresolve%2Fmain%2
                    Fconfig.json=&etag=%2272b987fd805cfa2b58c4c8c952b274a11bfd5a00%22'), (b'X-Powered-By',     
                    b'huggingface-moon'), (b'X-Request-Id',                                                    
                    b'Root=1-6a9851c9-238f55a45bc2597f2f6522af;7e29645f-d7d1-4cfa-8820-a1d3f3e789c1'),         
                    (b'RateLimit', b'"resolvers";r=2985;t=173'), (b'RateLimit-Policy', b'"fixed                
                    window";"resolvers";q=3000;w=300'), (b'cross-origin-opener-policy', b'same-origin'),       
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'), (b'Vary', b'Origin,
                    Accept'), (b'Access-Control-Expose-Headers',                                               
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Repo-Commit',            
                    b'1110a243fdf4706b3f48f1d95db1a4f5529b4d41'), (b'Accept-Ranges', b'bytes'),                
                    (b'X-HF-Warning', b'unauthenticated; Warning: You are sending unauthenticated requests to  
                    the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.'),    
                    (b'X-Hub-Cache', b'HIT'), (b'Content-Disposition', b'inline;                               
                    filename*=UTF-8\'\'config.json; filename="config.json";'), (b'Content-Security-Policy',    
                    b"default-src 'none'; sandbox"), (b'X-Linked-ETag',                                        
                    b'"72b987fd805cfa2b58c4c8c952b274a11bfd5a00"'), (b'X-Cache', b'Miss from cloudfront'),     
                    (b'Via', b'1.1 e4257444e1baa2e44ac1a48dd385109c.cloudfront.net (CloudFront)'),             
                    (b'X-Amz-Cf-Pop', b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'), (b'X-Amz-Cf-Id',     
                    b'MCS5ypvg3o1_Mu0-h7Da7MkorQsAL2AAiEBUNhJhVm7irKSCvfmdAw=='),                              
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'HEAD']>                                  
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'HEAD']>                                   
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'HEAD']>                                      
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'HEAD']>                               
           DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Content-Type',
                    b'text/plain; charset=utf-8'), (b'Content-Length', b'612'), (b'Connection', b'keep-alive'),
                    (b'Date', b'Mon, 01 Jun 2026 06:29:13 GMT'), (b'ETag',                                     
                    b'"72b987fd805cfa2b58c4c8c952b274a11bfd5a00"'), (b'X-Powered-By', b'huggingface-moon'),    
                    (b'X-Request-Id',                                                                          
                    b'Root=1-6a1d26b9-6cedbb9e6ebe2dae066c5d2c;a2c7e532-0dc7-4ea3-8085-aa1fbd025327'),         
                    (b'RateLimit', b'"resolvers";r=2770;t=197'), (b'RateLimit-Policy', b'"fixed                
                    window";"resolvers";q=3000;w=300'), (b'cross-origin-opener-policy', b'same-origin'),       
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'),                    
                    (b'Access-Control-Expose-Headers',                                                         
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Repo-Commit',            
                    b'1110a243fdf4706b3f48f1d95db1a4f5529b4d41'), (b'Accept-Ranges', b'bytes'),                
                    (b'X-Hub-Cache', b'MISS'), (b'Content-Disposition', b'inline;                              
                    filename*=UTF-8\'\'config.json; filename="config.json";'), (b'Content-Security-Policy',    
                    b"default-src 'none'; sandbox"), (b'Vary', b'Origin'), (b'X-Cache', b'Hit from             
                    cloudfront'), (b'Via', b'1.1 e4257444e1baa2e44ac1a48dd385109c.cloudfront.net               
                    (CloudFront)'), (b'X-Amz-Cf-Pop', b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'),      
                    (b'X-Amz-Cf-Id', b'9Mo9hH_x09qnnn_RtJ75xZtxEgSCVJp-8UybiiMKzA0IZrDxvkZbJQ=='), (b'Age',    
                    b'8071953'), (b'Strict-Transport-Security', b'max-age=31536000')])                         
           DEBUG    receive_response_body.started request=<Request [b'HEAD']>                                  
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'HEAD']>                                   
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'HEAD']>                                      
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'HEAD']>                               
[22:11:47] DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 307, b'Temporary Redirect',   
                    [(b'Content-Type', b'text/plain; charset=utf-8'), (b'Content-Length', b'300'),             
                    (b'Connection', b'keep-alive'), (b'Date', b'Wed, 02 Sep 2026 16:41:46 GMT'), (b'Location', 
                    b'/api/resolve-cache/models/sentence-transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d9
                    5db1a4f5529b4d41/tokenizer_config.json?%2Fsentence-transformers%2Fall-MiniLM-L6-v2%2Fresolv
                    e%2Fmain%2Ftokenizer_config.json=&etag=%22c79f2b6a0cea6f4b564fed1938984bace9d30ff0%22'),   
                    (b'X-Powered-By', b'huggingface-moon'), (b'X-Request-Id',                                  
                    b'Root=1-6a9851ca-679e9efb401c27050f4ffe6c;65a949e7-6c06-49d1-a418-ca73568f3e7e'),         
                    (b'RateLimit', b'"resolvers";r=2984;t=172'), (b'RateLimit-Policy', b'"fixed                
                    window";"resolvers";q=3000;w=300'), (b'cross-origin-opener-policy', b'same-origin'),       
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'), (b'Vary', b'Origin,
                    Accept'), (b'Access-Control-Expose-Headers',                                               
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Repo-Commit',            
                    b'1110a243fdf4706b3f48f1d95db1a4f5529b4d41'), (b'Accept-Ranges', b'bytes'),                
                    (b'X-Hub-Cache', b'HIT'), (b'Content-Disposition', b'inline;                               
                    filename*=UTF-8\'\'tokenizer_config.json; filename="tokenizer_config.json";'),             
                    (b'Content-Security-Policy', b"default-src 'none'; sandbox"), (b'X-Linked-ETag',           
                    b'"c79f2b6a0cea6f4b564fed1938984bace9d30ff0"'), (b'X-Cache', b'Miss from cloudfront'),     
                    (b'Via', b'1.1 e4257444e1baa2e44ac1a48dd385109c.cloudfront.net (CloudFront)'),             
                    (b'X-Amz-Cf-Pop', b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'), (b'X-Amz-Cf-Id',     
                    b'D-8Yl5zqrnbz2CRT_5Xqj5ikRy3ykFobAMyxFQlDI5ZFThmUsYe8tw=='),                              
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'HEAD']>                                  
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'HEAD']>                                   
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'HEAD']>                                      
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'HEAD']>                               
[22:11:48] DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Content-Type',
                    b'text/plain; charset=utf-8'), (b'Content-Length', b'350'), (b'Connection', b'keep-alive'),
                    (b'Date', b'Mon, 01 Jun 2026 06:29:13 GMT'), (b'ETag',                                     
                    b'"c79f2b6a0cea6f4b564fed1938984bace9d30ff0"'), (b'X-Powered-By', b'huggingface-moon'),    
                    (b'X-Request-Id',                                                                          
                    b'Root=1-6a1d26b9-3973fd0179761cf84b8cb0d4;9937d73e-673e-496d-893e-26ea1453e568'),         
                    (b'RateLimit', b'"resolvers";r=1173;t=175'), (b'RateLimit-Policy', b'"fixed                
                    window";"resolvers";q=3000;w=300'), (b'cross-origin-opener-policy', b'same-origin'),       
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'),                    
                    (b'Access-Control-Expose-Headers',                                                         
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Repo-Commit',            
                    b'1110a243fdf4706b3f48f1d95db1a4f5529b4d41'), (b'Accept-Ranges', b'bytes'),                
                    (b'X-Hub-Cache', b'MISS'), (b'Content-Disposition', b'inline;                              
                    filename*=UTF-8\'\'tokenizer_config.json; filename="tokenizer_config.json";'),             
                    (b'Content-Security-Policy', b"default-src 'none'; sandbox"), (b'Vary', b'Origin'),        
                    (b'X-Cache', b'Hit from cloudfront'), (b'Via', b'1.1                                       
                    e4257444e1baa2e44ac1a48dd385109c.cloudfront.net (CloudFront)'), (b'X-Amz-Cf-Pop',          
                    b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'), (b'X-Amz-Cf-Id',                       
                    b'wELgqbguABmn5P9nlTscAbuiqaCZmnfYdX5Wjf_chEhoIH7ZED52iQ=='), (b'Age', b'8071954'),        
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'HEAD']>                                  
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'GET']>                                    
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'GET']>                                       
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'GET']>                                
[22:11:49] DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 404, b'Not Found',            
                    [(b'Content-Type', b'application/json; charset=utf-8'), (b'Content-Length', b'64'),        
                    (b'Connection', b'keep-alive'), (b'Date', b'Wed, 02 Sep 2026 16:41:49 GMT'), (b'ETag',     
                    b'W/"40-09f9IAqP13xarAhQxFS2W8rvRkM"'), (b'X-Powered-By', b'huggingface-moon'),            
                    (b'X-Request-Id',                                                                          
                    b'Root=1-6a9851cd-71606f9154dc9d9e243622ad;3ba8dd29-28bb-418f-9f9c-3e01c021e62b'),         
                    (b'RateLimit', b'"api";r=498;t=169'), (b'RateLimit-Policy', b'"fixed                       
                    window";"api";q=500;w=300'), (b'cross-origin-opener-policy', b'same-origin'),              
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'), (b'Vary',          
                    b'Origin'), (b'Access-Control-Expose-Headers',                                             
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Error-Code',             
                    b'EntryNotFound'), (b'X-Error-Message', b'additional_chat_templates does not exist on      
                    "main"'), (b'X-Cache', b'Error from cloudfront'), (b'Via', b'1.1                           
                    e4257444e1baa2e44ac1a48dd385109c.cloudfront.net (CloudFront)'), (b'X-Amz-Cf-Pop',          
                    b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'), (b'X-Amz-Cf-Id',                       
                    b'sYoiP6a4vbnRYAiPNEW8NEwhzf3DvgTK80lPyX_ErP60JBW44hhiiw=='),                              
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'GET']>                                   
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'GET']>                                    
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'GET']>                                       
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'GET']>                                
[22:11:59] DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Content-Type',
                    b'application/json; charset=utf-8'), (b'Transfer-Encoding', b'chunked'), (b'Connection',   
                    b'keep-alive'), (b'Date', b'Wed, 02 Sep 2026 16:41:49 GMT'), (b'content-encoding',         
                    b'gzip'), (b'ETag', b'W/"1941-hVCCg8o6+Z9eHy795jGmhiAD0to"'), (b'X-Powered-By',            
                    b'huggingface-moon'), (b'X-Request-Id',                                                    
                    b'Root=1-6a9851cd-3cad246d7acee5600c613cfa;fc35ab48-7fd1-4cb7-a7da-1ae0f86891b8'),         
                    (b'RateLimit', b'"api";r=497;t=169'), (b'RateLimit-Policy', b'"fixed                       
                    window";"api";q=500;w=300'), (b'cross-origin-opener-policy', b'same-origin'),              
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'), (b'Vary',          
                    b'Origin'), (b'vary', b'Accept-Encoding'), (b'Access-Control-Expose-Headers',              
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Cache', b'Miss from      
                    cloudfront'), (b'Via', b'1.1 e4257444e1baa2e44ac1a48dd385109c.cloudfront.net               
                    (CloudFront)'), (b'X-Amz-Cf-Pop', b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'),      
                    (b'X-Amz-Cf-Id', b'xdyzoGZOnJ7DoP7JKx0FVsdNZ8YBiaR4fDu3Icfbl-h2yUfdNwpWgg=='),             
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'GET']>                                   
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'HEAD']>                                   
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'HEAD']>                                      
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'HEAD']>                               
           DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 307, b'Temporary Redirect',   
                    [(b'Content-Type', b'text/plain; charset=utf-8'), (b'Content-Length', b'304'),             
                    (b'Connection', b'keep-alive'), (b'Date', b'Wed, 02 Sep 2026 16:41:59 GMT'), (b'Location', 
                    b'/api/resolve-cache/models/sentence-transformers/all-MiniLM-L6-v2/1110a243fdf4706b3f48f1d9
                    5db1a4f5529b4d41/1_Pooling%2Fconfig.json?%2Fsentence-transformers%2Fall-MiniLM-L6-v2%2Freso
                    lve%2Fmain%2F1_Pooling%2Fconfig.json=&etag=%22d1514c3162bbe87b343f565fadc62e6c06f04f03%22')
                    , (b'X-Powered-By', b'huggingface-moon'), (b'X-Request-Id',                                
                    b'Root=1-6a9851d7-6f0bc4b36e6658490b7bbdf0;8504023a-65e7-4628-ba04-a709369b6fd8'),         
                    (b'RateLimit', b'"resolvers";r=2983;t=159'), (b'RateLimit-Policy', b'"fixed                
                    window";"resolvers";q=3000;w=300'), (b'cross-origin-opener-policy', b'same-origin'),       
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'), (b'Vary', b'Origin,
                    Accept'), (b'Access-Control-Expose-Headers',                                               
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Repo-Commit',            
                    b'1110a243fdf4706b3f48f1d95db1a4f5529b4d41'), (b'Accept-Ranges', b'bytes'),                
                    (b'X-HF-Warning', b'unauthenticated; Warning: You are sending unauthenticated requests to  
                    the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.'),    
                    (b'X-Hub-Cache', b'HIT'), (b'Content-Disposition', b'inline;                               
                    filename*=UTF-8\'\'config.json; filename="config.json";'), (b'Content-Security-Policy',    
                    b"default-src 'none'; sandbox"), (b'X-Linked-ETag',                                        
                    b'"d1514c3162bbe87b343f565fadc62e6c06f04f03"'), (b'X-Cache', b'Miss from cloudfront'),     
                    (b'Via', b'1.1 e4257444e1baa2e44ac1a48dd385109c.cloudfront.net (CloudFront)'),             
                    (b'X-Amz-Cf-Pop', b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'), (b'X-Amz-Cf-Id',     
                    b'gbPnNzKDHxzXKhO-iFQD_-Y6ECYkQwNxLY-swhH5gwD-KmqNYyBWcQ=='),                              
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'HEAD']>                                  
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'HEAD']>                                   
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'HEAD']>                                      
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'HEAD']>                               
[22:12:00] DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Content-Type',
                    b'text/plain; charset=utf-8'), (b'Content-Length', b'190'), (b'Connection', b'keep-alive'),
                    (b'Date', b'Thu, 06 Aug 2026 21:28:25 GMT'), (b'ETag',                                     
                    b'"d1514c3162bbe87b343f565fadc62e6c06f04f03"'), (b'X-Powered-By', b'huggingface-moon'),    
                    (b'X-Request-Id', b'Root=1-6a74fc79-2c42a0da3b8bf687496a9b3d'), (b'RateLimit',             
                    b'"resolvers";r=2997;t=23'), (b'RateLimit-Policy', b'"fixed                                
                    window";"resolvers";q=3000;w=300'), (b'cross-origin-opener-policy', b'same-origin'),       
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'),                    
                    (b'Access-Control-Expose-Headers',                                                         
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Repo-Commit',            
                    b'1110a243fdf4706b3f48f1d95db1a4f5529b4d41'), (b'Accept-Ranges', b'bytes'),                
                    (b'Content-Disposition', b'inline; filename*=UTF-8\'\'config.json;                         
                    filename="config.json";'), (b'Content-Security-Policy', b"default-src 'none'; sandbox"),   
                    (b'Vary', b'Origin'), (b'X-Cache', b'Hit from cloudfront'), (b'Via', b'1.1                 
                    e4257444e1baa2e44ac1a48dd385109c.cloudfront.net (CloudFront)'), (b'X-Amz-Cf-Pop',          
                    b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'), (b'X-Amz-Cf-Id',                       
                    b'Y0G77UtOiUnUkKuy0DXjeAtTs-uKMSfMJ3nTsqUu1dLqUzcK2zYECQ=='), (b'Age', b'2315615'),        
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'HEAD']>                                  
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           DEBUG    send_request_headers.started request=<Request [b'GET']>                                    
           DEBUG    send_request_headers.complete                                                              
           DEBUG    send_request_body.started request=<Request [b'GET']>                                       
           DEBUG    send_request_body.complete                                                                 
           DEBUG    receive_response_headers.started request=<Request [b'GET']>                                
[22:12:18] DEBUG    receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Content-Type',
                    b'application/json; charset=utf-8'), (b'Transfer-Encoding', b'chunked'), (b'Connection',   
                    b'keep-alive'), (b'Date', b'Wed, 02 Sep 2026 16:42:00 GMT'), (b'content-encoding',         
                    b'gzip'), (b'ETag', b'W/"1bb0-bf0HGFAQlf5Wn5eMsL/ZXR9+fIU"'), (b'X-Powered-By',            
                    b'huggingface-moon'), (b'X-Request-Id',                                                    
                    b'Root=1-6a9851d8-6a4a7eaa0b2ddd0f15ef3381;37ad1fd2-9c97-4f5e-b5ef-2001b6cb916a'),         
                    (b'RateLimit', b'"api";r=496;t=158'), (b'RateLimit-Policy', b'"fixed                       
                    window";"api";q=500;w=300'), (b'cross-origin-opener-policy', b'same-origin'),              
                    (b'Referrer-Policy', b'strict-origin-when-cross-origin'), (b'Access-Control-Max-Age',      
                    b'86400'), (b'Access-Control-Allow-Origin', b'https://huggingface.co'), (b'Vary',          
                    b'Origin'), (b'vary', b'Accept-Encoding'), (b'Access-Control-Expose-Headers',              
                    b'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ra
                    nges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash'), (b'X-Cache', b'Miss from      
                    cloudfront'), (b'Via', b'1.1 e4257444e1baa2e44ac1a48dd385109c.cloudfront.net               
                    (CloudFront)'), (b'X-Amz-Cf-Pop', b'BLR50-P4'), (b'Alt-Svc', b'h3=":443"; ma=86400'),      
                    (b'X-Amz-Cf-Id', b'WaGY4swmYHVu_S084qEsMTu8sexnJgkewa7bsxwi0B9ShwhhACeZRQ=='),             
                    (b'Strict-Transport-Security', b'max-age=31536000')])                                      
           DEBUG    receive_response_body.started request=<Request [b'GET']>                                   
           DEBUG    receive_response_body.complete                                                             
           DEBUG    response_closed.started                                                                    
           DEBUG    response_closed.complete                                                                   
           INFO     Embedding model loaded.                                                                    
[22:12:27] INFO     ChromaDB collection ready at data/chroma_db                                                
Traceback (most recent call last):
  File "F:\fyj\main.py", line 280, in <module>
    cli()
  File "F:\fyj\venv\Lib\site-packages\click\core.py", line 1524, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\fyj\venv\Lib\site-packages\click\core.py", line 1445, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "F:\fyj\venv\Lib\site-packages\click\core.py", line 1912, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\fyj\venv\Lib\site-packages\click\core.py", line 1308, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\fyj\venv\Lib\site-packages\click\core.py", line 877, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\fyj\main.py", line 76, in run
    final_state = run_pipeline(
                  ^^^^^^^^^^^^^
  File "F:\fyj\graph\orchestrator.py", line 420, in run_pipeline
    final_state = app.invoke(initial_state)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\fyj\venv\Lib\site-packages\langgraph\pregel\main.py", line 3928, in invoke
    for chunk in self.stream(
  File "F:\fyj\venv\Lib\site-packages\langgraph\pregel\main.py", line 2982, in stream
    for _ in runner.tick(
  File "F:\fyj\venv\Lib\site-packages\langgraph\pregel\_runner.py", line 207, in tick
    run_with_retry(
  File "F:\fyj\venv\Lib\site-packages\langgraph\pregel\_retry.py", line 617, in run_with_retry
    return task.proc.invoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\fyj\venv\Lib\site-packages\langgraph\_internal\_runnable.py", line 684, in invoke
    input = context.run(step.invoke, input, config, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\fyj\venv\Lib\site-packages\langgraph\_internal\_runnable.py", line 426, in invoke
    ret = self.func(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\fyj\venv\Lib\site-packages\langgraph\prebuilt\tool_node.py", line 799, in _func
    tool_calls, input_type = self._parse_input(input)
                             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\fyj\venv\Lib\site-packages\langgraph\prebuilt\tool_node.py", line 1255, in _parse_input
    raise ValueError(msg)
ValueError: No message found in input
During task with name 'tool_execution' and id '62286047-e66d-86af-eab1-f9fa60a25e88'
[22:12:29] DEBUG    close.started                                                                              
           DEBUG    close.complete   