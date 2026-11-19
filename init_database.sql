-- 创建项目数据库，如果已经存在就跳过
-- utf8mb4 支持中文和表情符号
create database if not exists scraping_to_analysis
    character set utf8mb4;

-- 选择接下来要操作的数据库
use scraping_to_analysis;

-- 创建商品采集记录表，如果已经存在就跳过
create table if not exists product_snapshots (
    -- 记录编号：自动递增，作为每条记录的唯一标识
    id bigint unsigned auto_increment primary key,

    -- 淘宝商品 id：同一个商品可以有多次采集记录
    product_id varchar(64),

    -- 商品名称：不能为空
    name text not null,

    -- 页面展示价格：最多 12 位数字，其中 2 位为小数，不能为空
    display_price decimal(12, 2) not null,

    -- 价格说明：例如“国补后”“优惠后”
    price_note varchar(255),

    -- 商品详情链接
    detail_url text,

    -- 实际采集时间：不知道时可以留空
    collected_at datetime,

    -- 导入数据库的时间：不手动填写时，自动记录当前时间
    imported_at datetime not null default current_timestamp
);

-- 查看表结构，包括字段名称、类型等信息
describe product_snapshots;

-- 查询商品采集记录的总条数
select count(*) as 商品数量
from product_snapshots;

-- 确认数据库中的记录总数
select count(*) as 商品数量
from scraping_to_analysis.product_snapshots;

-- 查看前 5 条商品，按记录编号排序
select
    id as 编号,
    name as 商品名称,
    display_price as 展示价格,
    price_note as 价格说明
from scraping_to_analysis.product_snapshots
order by id
limit 5;

-- 筛选展示价格在 5000～8000 元之间的商品
select
    id as 编号,
    name as 商品名称,
    display_price as 展示价格,
    price_note as 价格说明
from scraping_to_analysis.product_snapshots
where display_price between 5000 and 8000
order by display_price asc;

-- 统计当前全部商品的展示价格
select
    count(*) as 商品数量,
    round(avg(display_price), 2) as 平均价格,
    min(display_price) as 最低价格,
    max(display_price) as 最高价格
from scraping_to_analysis.product_snapshots;

-- 按价格说明分组，缺失值显示为“未标注”
select
    coalesce(price_note, '未标注') as 价格说明,
    count(*) as 商品数量,
    round(avg(display_price), 2) as 平均价格
from scraping_to_analysis.product_snapshots
group by coalesce(price_note, '未标注')
order by 商品数量 desc;

-- 先按展示价格划分区间，再统计每个区间的数量和均价
select
    case
        when display_price < 3000 then '低于3000'
        when display_price < 5000 then '3000至不足5000'
        when display_price < 8000 then '5000至不足8000'
        else '8000及以上'
    end as 价格区间,
    count(*) as 商品数量,
    round(avg(display_price), 2) as 平均价格
from scraping_to_analysis.product_snapshots
group by 价格区间
-- 对分组统计后的结果进行筛选
having count(*) >= 10
order by min(display_price);

-- 查找名称中包含“联想”的商品，按价格从低到高排列
select
    id as 编号,
    name as 商品名称,
    display_price as 展示价格
from scraping_to_analysis.product_snapshots
where name like '%联想%'
order by display_price asc;

-- 同时满足名称条件和价格条件
select
    id as 编号,
    name as 商品名称,
    display_price as 展示价格
from scraping_to_analysis.product_snapshots
where name like '%联想%'
    and display_price between 5000 and 8000
order by display_price asc;

-- 联想或华硕，同时满足价格范围
select
    id as 编号,
    name as 商品名称,
    display_price as 展示价格
from scraping_to_analysis.product_snapshots
where (name like '%联想%' or name like '%华硕%')
    and display_price between 5000 and 8000
order by display_price asc;

-- 查找符合条件的商品，显示价格最高的前 3 条
select
    name as 商品名称,
    display_price as 展示价格
from scraping_to_analysis.product_snapshots
where name like '%机械革命%'
    and display_price < 6000
order by display_price desc, id asc
limit 3;

-- 查找没有价格说明的商品
select
    id as 编号,
    name as 商品名称,
    display_price as 展示价格
from scraping_to_analysis.product_snapshots
where price_note is null
order by id;

-- 按商品名称分组，只显示出现超过一次的名称
select
    name as 商品名称,
    count(*) as 出现次数,
    min(display_price) as 最低展示价格,
    max(display_price) as 最高展示价格
from scraping_to_analysis.product_snapshots
group by name
having count(*) > 1;

-- 外层查询：显示同名商品的具体记录
select
    id as 编号,
    name as 商品名称,
    display_price as 展示价格,
    detail_url as 商品链接
from scraping_to_analysis.product_snapshots
where name in (
    -- 内层查询：找出出现超过一次的商品名称
    select name
    from scraping_to_analysis.product_snapshots
    group by name
    having count(*) > 1
)
order by name, id;

-- 查找展示价格高于样本均价的商品
select
    id as 编号,
    name as 商品名称,
    display_price as 展示价格
from scraping_to_analysis.product_snapshots
where display_price > (
    -- 计算全部商品的平均展示价格
    select avg(display_price)
    from scraping_to_analysis.product_snapshots
)
order by display_price asc, id asc;

-- 统计高于整体均价的商品
select
    count(*) as 商品数量,
    round(avg(display_price), 2) as 平均展示价格
from scraping_to_analysis.product_snapshots
where display_price > (
    -- 计算全部商品的平均展示价格
    select avg(display_price)
    from scraping_to_analysis.product_snapshots
);

-- 创建人工核查备注表
create table if not exists scraping_to_analysis.product_reviews (
    -- 每条备注的唯一编号
    id bigint unsigned auto_increment primary key,

    -- 对应商品采集记录的编号，类型与原表 id 一致
    snapshot_id bigint unsigned not null,

    -- 人工填写的备注
    review_note varchar(255) not null,

    -- 自动记录备注创建时间
    created_at datetime not null default current_timestamp,

    -- 外键：确保备注对应的采集记录确实存在
    foreign key (snapshot_id)
        references scraping_to_analysis.product_snapshots(id)
);

-- 添加人工核查备注，不修改原始采集数据
insert into scraping_to_analysis.product_reviews
    (snapshot_id, review_note)
values
    (17, '与编号29名称相同，待核查是否为同一商品'),
    (29, '与编号17名称相同，展示价格不同，暂不删除');

-- 将商品采集记录与核查备注关联起来
select
    p.id as 采集记录编号,
    p.name as 商品名称,
    p.display_price as 展示价格,
    r.review_note as 核查备注
from scraping_to_analysis.product_snapshots as p
inner join scraping_to_analysis.product_reviews as r
    on p.id = r.snapshot_id
order by p.id, r.id;

-- 显示全部采集记录，同时匹配核查备注
select
    p.id as 采集记录编号,
    p.name as 商品名称,
    p.display_price as 展示价格,
    r.review_note as 核查备注
from scraping_to_analysis.product_snapshots as p
left join scraping_to_analysis.product_reviews as r
    on p.id = r.snapshot_id
order by p.id, r.id;

-- 查询没有任何核查备注的商品
select
    p.id as 采集记录编号,
    p.name as 商品名称,
    p.display_price as 展示价格,
    r.review_note as 核查备注
from scraping_to_analysis.product_snapshots as p
left join scraping_to_analysis.product_reviews as r
    on p.id = r.snapshot_id
where r.id is null
order by p.id;

-- 统计每条采集记录对应的备注数量
select
    p.id as 采集记录编号,
    p.name as 商品名称,
    count(r.id) as 备注数量
from scraping_to_analysis.product_snapshots as p
left join scraping_to_analysis.product_reviews as r
    on p.id = r.snapshot_id
group by p.id, p.name
order by 备注数量 desc, p.id asc;

-- 查找低于 3000 元且没有备注的商品
select
    p.id as 采集记录编号,
    p.name as 商品名称,
    p.display_price as 展示价格
from scraping_to_analysis.product_snapshots as p
left join scraping_to_analysis.product_reviews as r
    on p.id = r.snapshot_id
where r.id is null
    and p.display_price < 3000
order by p.display_price asc, p.id asc
limit 5;

-- 为编号 17 添加第二条备注，仅执行一次
insert into scraping_to_analysis.product_reviews
    (snapshot_id, review_note)
values
    (17, '练习备注：仍需核查商品详情与配置');

-- 查看编号 17 的商品信息及全部备注
select
    p.id as 采集记录编号,
    p.name as 商品名称,
    r.id as 备注编号,
    r.review_note as 核查备注
from scraping_to_analysis.product_snapshots as p
inner join scraping_to_analysis.product_reviews as r
    on p.id = r.snapshot_id
where p.id = 17
order by r.id;

-- 比较关联结果行数、有备注的商品数和备注条数
select
    count(*) as 关联结果行数,
    count(distinct p.id) as 有备注的商品数,
    count(r.id) as 备注条数
from scraping_to_analysis.product_snapshots as p
inner join scraping_to_analysis.product_reviews as r
    on p.id = r.snapshot_id;

-- 将同一条采集记录的多条备注合并显示
select
    p.id as 采集记录编号,
    p.name as 商品名称,
    count(r.id) as 备注数量,
    group_concat(
        r.review_note
        order by r.id
        separator '；'
    ) as 全部备注
from scraping_to_analysis.product_snapshots as p
inner join scraping_to_analysis.product_reviews as r
    on p.id = r.snapshot_id
group by p.id, p.name
order by p.id;

-- 创建清洗视图：保留原始数据，通过视图统一展示格式
create or replace view scraping_to_analysis.cleaned_product_snapshots as
select
    id,

    -- 去掉商品 id 两端空格，空字符串转换为 null
    nullif(trim(product_id), '') as product_id,

    -- 去掉名称两端空格，缺失或空名称显示为“未命名商品”
    coalesce(nullif(trim(name), ''), '未命名商品') as name,

    -- 原字段已经是保留两位小数的 decimal 类型
    display_price,

    -- 去掉价格说明两端空格，将缺失值和空字符串统一显示
    coalesce(nullif(trim(price_note), ''), '未标注') as price_note,

    -- 去掉链接两端空格，空链接转换为 null
    nullif(trim(detail_url), '') as detail_url,

    -- 保留实际采集时间和导入时间
    collected_at,
    imported_at
from scraping_to_analysis.product_snapshots;

-- 检查清洗结果的记录数量与价格
select
    count(*) as 商品数量,
    round(avg(display_price), 2) as 平均价格,
    min(display_price) as 最低价格,
    max(display_price) as 最高价格
from scraping_to_analysis.cleaned_product_snapshots;

-- 检查清洗后的价格说明
select
    price_note as 价格说明,
    count(*) as 商品数量
from scraping_to_analysis.cleaned_product_snapshots
group by price_note
order by 商品数量 desc;
