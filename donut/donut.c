#include <math.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

// gcc donut.c -lm -o donut

int k;
const float theta_spacing = 0.07; // θ 角度，圆环的横截面圆周，垂直平面
const float phi_spacing = 0.02; // φ 角度，圆环的旋转中心，水平平面

void main() {
    float rotation_X = 0; // rotation about the x-axis
    float rotation_Z = 0; // rotation about the z-axis
    float phi, theta;
    float zbuff[1760];  // Z buffer of 80 * 22
    char txtbuff[1760]; // text buffer of 80 * 22

    printf("\x1b[2J"); // clear screen
    for (;;) {
        memset(txtbuff, 32, 1760);
        memset(zbuff, 0, 7040);
        // theta 绕着圆环的横截面圆
        // for (theta = 0; 6.28 > theta; theta += theta_spacing)
            // phi 绕着圆环的旋转中心
            // for (phi = 0; 6.28 > phi; phi += phi_spacing) 
            {
                float c = sin(phi); // 截面圆心在Y轴的偏移率
                float d =
                    cos(theta); // 截面圆周上的点在水平方向X轴上的原始偏移率
                float e = sin(rotation_X); // 垂直方向上旋转偏移度
                float f =
                    sin(theta); // 截面圆周上的点，在垂直方向Z轴上的原始偏移率
                float g = cos(rotation_X);
                float h = d + 2;
                float D = 1 / (c * h * e + f * g + 5); // 计算亮度
                float l = cos(phi); // 截面圆心在X轴的偏移率
                float m = cos(rotation_Z);
                float n = sin(rotation_Z);
                float t = c * h * g - f * e;
                int x = 40 + 30 * D * (l * h * m - t * n); // X坐标
                int y = 12 + 15 * D * (l * h * n + t * m); // Y坐标
                int o = x + 80 * y;                        // 字符缓冲偏移
                int N = 8 * ((f * e - c * d * g) * m - c * d * e - f * g -
                             l * d * n);
                if (22 > y && y > 0 && x > 0 && 80 > x && D > zbuff[o]) {
                    zbuff[o] = D;
                    txtbuff[o] = ".,-~:;=!*#$@"[N > 0 ? N : 0];
                }
            }
        printf("\x1b[H");
        for (k = 0; 1761 > k; k++)
            putchar(k % 80 ? txtbuff[k] : 10);
        rotation_X += 0.04;
        rotation_Z += 0.02;
        usleep(1000 * 10);
    }
}
