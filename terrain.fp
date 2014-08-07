// Copyright (c) 2014 Per Lindstrand

uniform sampler2D tex;

varying float shade;

void main()
{
    gl_FragColor = shade * texture2D(tex, gl_TexCoord[0].st);
}
