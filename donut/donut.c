#include <stdio.h>
#include <math.h>
#include <string.h>
#include <unistd.h>

int k;

void main()
{
    float A = 0;
    float B = 0;
    float i, j;
    float z[1760];
    char b[1760];

    printf("\x1b[2J");
    for (;;)
    {
        memset(b, 32, 1760);
        memset(z, 0, 7040);
        for (j = 0; 6.28 > j; j += 0.07)
            for (i = 0; 6.28 > i; i += 0.02)
            {
                float c = sin(i);
                float d = cos(j);
                float e = sin(A);
                float f = sin(j);
                float g = cos(A);
                float h = d + 2;
                float D = 1 / (c * h * e + f * g + 5);
                float l = cos(i);
                float m = cos(B);
                float n = sin(B);
                float t = c * h * g - f * e;
                int x = 40 + 30 * D * (l * h * m - t * n);
                int y = 12 + 15 * D * (l * h * n + t * m);
                int o = x + 80 * y;
                int N = 8 * ((f * e - c * d * g) * m - c * d * e - f * g - l * d * n);
                if (22 > y && y > 0 && x > 0 && 80 > x && D > z[o])
                {
                    z[o] = D;
                    b[o] = ".,-~:;=!*#$@"[N > 0 ? N : 0];
                }
            }
        printf("\x1b[H");
        for (k = 0; 1761 > k; k++)
            putchar(k % 80 ? b[k] : 10);
        A += 0.04;
        B += 0.02;
        usleep(1000 * 10);
    }
}

// const float theta_spacing = 0.07;
// const float phi_spacing = 0.02;

// const float R1 = 1;
// const float R2 = 2;
// const float K2 = 5;
// // Calculate K1 based on screen size: the maximum x-distance occurs
// // roughly at the edge of the torus, which is at x=R1+R2, z=0.  we
// // want that to be displaced 3/8ths of the width of the screen, which
// // is 3/4th of the way from the center to the side of the screen.
// // screen_width*3/8 = K1*(R1+R2)/(K2+0)
// // screen_width*K2*3/(8*(R1+R2)) = K1
// const float K1 = screen_width * K2 * 3 / (8 * (R1 + R2));

// render_frame(float A, float B)
// {
//     // precompute sines and cosines of A and B
//     float cosA = cos(A), sinA = sin(A);
//     float cosB = cos(B), sinB = sin(B);

//     char output[0..screen_width, 0..screen_height] = ' ';
//     float zbuffer[0..screen_width, 0..screen_height] = 0;

//     // theta goes around the cross-sectional circle of a torus
//     for (float theta = 0; theta < 2 * pi; theta += theta_spacing)
//     {
//         // precompute sines and cosines of theta
//         float costheta = cos(theta), sintheta = sin(theta);

//         // phi goes around the center of revolution of a torus
//         for (float phi = 0; phi < 2 * pi; phi += phi_spacing)
//         {
//             // precompute sines and cosines of phi
//             float cosphi = cos(phi), sinphi = sin(phi);

//             // the x,y coordinate of the circle, before revolving (factored
//             // out of the above equations)
//             float circlex = R2 + R1 * costheta;
//             float circley = R1 * sintheta;

//             // final 3D (x,y,z) coordinate after rotations, directly from
//             // our math above
//             float x = circlex * (cosB * cosphi + sinA * sinB * sinphi) - circley * cosA * sinB;
//             float y = circlex * (sinB * cosphi - sinA * cosB * sinphi) + circley * cosA * cosB;
//             float z = K2 + cosA * circlex * sinphi + circley * sinA;
//             float ooz = 1 / z; // "one over z"

//             // x and y projection.  note that y is negated here, because y
//             // goes up in 3D space but down on 2D displays.
//             int xp = (int)(screen_width / 2 + K1 * ooz * x);
//             int yp = (int)(screen_height / 2 - K1 * ooz * y);

//             // calculate luminance.  ugly, but correct.
//             float L = cosphi * costheta * sinB - cosA * costheta * sinphi -
//                       sinA * sintheta + cosB * (cosA * sintheta - costheta * sinA * sinphi);
//             // L ranges from -sqrt(2) to +sqrt(2).  If it's < 0, the surface
//             // is pointing away from us, so we won't bother trying to plot it.
//             if (L > 0)
//             {
//                 // test against the z-buffer.  larger 1/z means the pixel is
//                 // closer to the viewer than what's already plotted.
//                 if (ooz > zbuffer[xp, yp])
//                 {
//                     zbuffer[xp, yp] = ooz;
//                     int luminance_index = L * 8;
//                     // luminance_index is now in the range 0..11 (8*sqrt(2) = 11.3)
//                     // now we lookup the character corresponding to the
//                     // luminance and plot it in our output:
//                     output[xp, yp] = ".,-~:;=!*#$@"[luminance_index];
//                 }
//             }
//         }
//     }

//     // now, dump output[] to the screen.
//     // bring cursor to "home" location, in just about any currently-used
//     // terminal emulation mode
//     printf("\x1b[H");
//     for (int j = 0; j < screen_height; j++)
//     {
//         for (int i = 0; i < screen_width; i++)
//         {
//             putchar(output[i, j]);
//         }
//         putchar('\n');
//     }
// }