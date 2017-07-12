# FRAPanalyzer
New ways to analyze FRAP images.



## INSTALLATION
If you want to save animations you should install ffmpeg:
`brew install ffmpeg`
jupyter nbextension enable --py --sys-prefix widgetsnbextension


## Общие слова о том, что уже есть

### Общее
Вот общие обзорчики стандартных подходов, которые основаны на оптимизации “Смаз - градиента“. Вроде все на пальцах
*  http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.402.1860&rep=rep1&type=pdf
*http://www.cscjournals.org/manuscript/Journals/IJIP/Volume3/Issue1/IJIP-15.pdf

### По поводу фильтров собеля.
* Здесь описывают какой классный фильтр Собеля, но потом такие: “Шум все портит, надо что - то делать” - придумали вставить “мягкий пороговый вейвлет против шума“.
http://sci-hub.cc/10.1109/ICCSIT.2010.5563693

* Очень крутая статья как минимум ссылками на другие статьи. В самом  introduction уже говорится о нескольких крутых подходах, например, о решении связанном с близостью в Гильбертовом пространстве и много еще всего более интересного, в том числе базовый подход (это лишь частный оптимизированный для онлайн решения случай). В самой же статье описывается комбинация операторов Собеля и Зерники. Суть в том, что второй оператор позволяет как бы убрать ложные точки на границе контура за счет того, что он не чувствителен к шуму.  
http://linkinghub.elsevier.com.sci-hub.cc/retrieve/pii/S0262885604001660

### По поводу фильтров Канни.
Еще раз, Канни - это не совсем фильтр, скорее комбинация из шагов, где каждый шаг поддается сомнению и может быть оптимизирован, начиная со Смаза (варианты) .
Вот некоторые вариации:

* Размер оператора расширен до 3 на 3, говорится о большей устойсивости к шуму.
http://sci-hub.cc/10.1109/ICMA.2014.6885761
* Если все скалить, то тоже говорят лучше
http://sci-hub.cc/10.1109/TPAMI.2005.173


Теперь о других подходах. И немного о том, на что можно еще опереться Вот некотрые из них:
* http://sci-hub.cc/10.1109/34.56205
* http://sci-hub.cc/10.1109/76.905991
* http://sci-hub.cc/10.1109/TPAMI.2004.1273918
* http://sci-hub.cc/10.1007/s00500-005-0511-y
* http://sci-hub.cc/10.1109/CVPR.1997.609409
* http://sci-hub.cc/10.1109/ICHIT.2008.224


[![Filters on boundaries of ROI](https://preview.ibb.co/cweoAk/2017_05_16_12_55_58.png)](https://youtu.be/phfgszzy4mQ)
