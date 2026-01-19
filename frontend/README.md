# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).


# 프로젝트 설정

## 필수 패키지 
  - @tanstack/react-query (v5.90.19) 
  - 서버 상태 관리
  - axios (v1.13.2) - HTTP 클라이언트
  - tailwindcss (v4.1.18) + @tailwindcss/postcss - CSS 프레임워크
  - class-variance-authority, clsx, tailwind-merge - shadcn/ui 유틸리티
  - lucide-react - 아이콘 라이브러리

## 프로젝트 구조
  - src/components/ - React 컴포넌트
  - src/components/ui/ - shadcn/ui 기본 컴포넌트 (Button, Input)
  - src/api/ - API 클라이언트
  - src/hooks/ - 커스텀 훅
  - src/types/ - TypeScript 타입 정의
  - src/lib/ - 유틸리티 함수

## 설정 파일:
  - TanStack Query Provider 설정 (main.tsx)
  - ailwind CSS 설정 (tailwind.config.js, postcss.config.js)
  - Path alias 설정 (@/* → ./src/*)
  - TypeScript 설정 업데이트